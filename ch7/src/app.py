"""Main FastAPI application for Hybrid RAG."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import asyncio

from .config import get_settings, wait_for_elasticsearch
from .rag.hybridrag import HybridRAGSuperComponent
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Hybrid RAG API",
    description="A FastAPI application that provides hybrid retrieval-augmented generation using Elasticsearch and OpenAI",
    version="1.0.0"
)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str

class Document(BaseModel):
    content: str
    meta: Dict[str, Any] = {}

class QueryResponse(BaseModel):
    answer: str
    documents: List[Document]
    query: str

# Global variable to store the hybrid RAG component
hybrid_rag_component: Optional[HybridRAGSuperComponent] = None
indexing_in_progress = False


@app.on_event("startup")
async def startup_event():
    """Initialize the Hybrid RAG component on startup."""
    global hybrid_rag_component
    
    try:
        logger.info("Starting up Hybrid RAG API...")
        
        # Wait for Elasticsearch to be available
        if not wait_for_elasticsearch(settings.elasticsearch_host):
            raise ConnectionError(f"Could not connect to Elasticsearch at {settings.elasticsearch_host}")
        
        logger.info("Initializing Elasticsearch document store...")
        
        # Initialize the document store
        document_store = ElasticsearchDocumentStore(
            hosts=settings.elasticsearch_host,
            index=settings.elasticsearch_index
        )
        
        logger.info("Initializing Hybrid RAG SuperComponent...")
        
        # Create the Hybrid RAG SuperComponent
        hybrid_rag_component = HybridRAGSuperComponent(
            document_store=document_store,
            embedder_model=settings.embedder_model,
            llm_model=settings.llm_model,
            top_k=settings.top_k,
            ranker_model=settings.ranker_model,
            openai_api_key=settings.openai_api_key
        )
        
        logger.info("Hybrid RAG component initialized successfully!")
        
        
    except Exception as e:
        logger.error(f"Failed to initialize Hybrid RAG component: {str(e)}")
        raise e


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Hybrid RAG API...")


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Hybrid RAG API",
        "version": "1.0.0", 
        "status": "running",
        "elasticsearch_host": settings.elasticsearch_host,
        "elasticsearch_available": wait_for_elasticsearch(settings.elasticsearch_host, max_retries=1),
        "component_initialized": hybrid_rag_component is not None,
        "endpoints": {
            "query": "/query",
            "health": "/health",
            "info": "/info",
            "indexing": "/indexing",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    elasticsearch_available = wait_for_elasticsearch(settings.elasticsearch_host, max_retries=1)
    component_ready = hybrid_rag_component is not None
    
    status = "healthy" if (elasticsearch_available and component_ready) else "unhealthy"
    
    return {
        "status": status,
        "elasticsearch_available": elasticsearch_available,
        "elasticsearch_host": settings.elasticsearch_host,
        "component_initialized": component_ready,
        "indexing_in_progress": indexing_in_progress
    }


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the hybrid RAG system with a question."""
    if hybrid_rag_component is None:
        raise HTTPException(
            status_code=503, 
            detail="Hybrid RAG component not initialized. Please check the logs for initialization errors."
        )
    
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Run the hybrid RAG pipeline
        result = hybrid_rag_component.run(query=request.query)
        
        # Extract the answer
        answer = result.get("replies", ["No answer generated"])[0]
        
        # Process the retrieved documents
        documents = []
        for doc in result.get("documents", []):
            documents.append(Document(
                content=doc.content,
                score=getattr(doc, 'score', None),
                meta=doc.meta
            ))
        
        logger.info(f"Query processed successfully. Retrieved {len(documents)} documents.")
        
        return QueryResponse(
            answer=answer,
            documents=documents,
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing query: {str(e)}"
        )




@app.get("/info")
async def get_info():
    """Get information about the current configuration."""
    if hybrid_rag_component is None:
        raise HTTPException(status_code=503, detail="Hybrid RAG component not initialized")
    
    return {
        "embedder_model": settings.embedder_model,
        "llm_model": settings.llm_model,
        "top_k": settings.top_k,
        "ranker_model": settings.ranker_model,
        "elasticsearch_host": settings.elasticsearch_host,
        "elasticsearch_index": settings.elasticsearch_index,
        "elasticsearch_available": wait_for_elasticsearch(settings.elasticsearch_host, max_retries=1)
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "src.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )