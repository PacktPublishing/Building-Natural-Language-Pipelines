from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bytewax.dataflow import Dataflow
from bytewax.run import cli_main
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
import asyncio
import logging
import os

from indexing_dataflow import run_pipeline_with_symbol  # Your Bytewax indexing pipeline
from querying import RetrieveDocuments  # Your query pipeline logic

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Global tasks dictionary to track active Bytewax flows
active_tasks = {}

# Request model for query
class QueryRequest(BaseModel):
    symbols: str  # Comma-separated list of symbols
    question: str  # Natural language query


@app.post("/query/")
async def process_query(request: QueryRequest):
    """
    Index symbols using Bytewax and query the in-memory document store.
    """
    # Parse symbols
    symbols = [symbol.strip() for symbol in request.symbols.split(",") if symbol.strip()]
    if not symbols:
        raise HTTPException(status_code=400, detail="At least one symbol must be provided.")

    # Create a new in-memory document store for this session
    document_store = InMemoryDocumentStore()

    # Start Bytewax dataflow for each symbol
    def run_bytewax(symbol):
        """Run Bytewax for a given symbol."""
        try:
            flow = run_pipeline_with_symbol(symbol, document_store, OPENAI_API_KEY)
            cli_main(flow)
        except Exception as e:
            logger.error(f"Error in Bytewax flow for symbol '{symbol}': {e}")
            raise

    # Run Bytewax flows concurrently for all symbols
    tasks = [asyncio.to_thread(run_bytewax, symbol) for symbol in symbols]
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running Bytewax dataflow: {e}")

    # Initialize query pipeline with the populated document store
    query_pipeline = RetrieveDocuments(document_store, OPENAI_API_KEY)

    # Use the pipeline to query
    try:
        response = query_pipeline.run({"text_embedder": {"text": request.question}, "prompt_builder": {"question": request.question}})
        return {"answer": response["llm"]["replies"][0]}
    except Exception as e:
        logger.error(f"Error querying the pipeline: {e}")
        raise HTTPException(status_code=500, detail="Error querying the pipeline.")


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "API is running"}
