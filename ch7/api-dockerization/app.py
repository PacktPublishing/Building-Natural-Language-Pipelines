from haystack.document_stores.in_memory import InMemoryDocumentStore
import os
from dotenv import load_dotenv
from indexing_dataflow import run_pipeline_with_symbol
load_dotenv(".env")
open_ai_key = os.environ.get("OPENAI_API_KEY")

# Example usage
user_symbol = "AAPL" 
document_store = InMemoryDocumentStore()
flow = run_pipeline_with_symbol(user_symbol, document_store, open_ai_key)
