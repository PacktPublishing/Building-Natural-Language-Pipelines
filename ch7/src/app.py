"""Main FastAPI application for Hybrid RAG."""

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from .config import get_settings
from .rag.hybridrag import HybridRAGSuperComponent
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    """Validate API key from request header."""
    if api_key != settings.rag_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )
    return api_key

# Initialize FastAPI app
app = FastAPI(
    title="Hybrid RAG API",
    description="A FastAPI application that provides hybrid retrieval-augmented generation using Qdrant and OpenAI",
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
        
        logger.info("Initializing Qdrant document store...")
        
        # Initialize the document store
        document_store = QdrantDocumentStore(
            path=settings.qdrant_path,
            index=settings.qdrant_index,
            embedding_dim=1536,  # text-embedding-3-small dimension
            recreate_index=False,
            use_sparse_embeddings=True  # Enable sparse embeddings for hybrid retrieval
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
        "qdrant_path": settings.qdrant_path,
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
    component_ready = hybrid_rag_component is not None
    
    status = "healthy" if component_ready else "unhealthy"
    
    return {
        "status": status,
        "qdrant_path": settings.qdrant_path,
        "component_initialized": component_ready,
        "indexing_in_progress": indexing_in_progress
    }


@app.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    api_key: str = Depends(get_api_key)
):
    """Query the hybrid RAG system with a question. Requires valid API key."""
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
        "qdrant_path": settings.qdrant_path,
        "qdrant_index": settings.qdrant_index
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