
from haystack import Pipeline
from haystack.components.embedders import OpenAITextEmbedder 
from haystack.utils import Secret
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.components.readers import ExtractiveReader
from haystack.document_stores.in_memory import InMemoryDocumentStore

from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv(".env")
open_ai_key = os.environ.get("OPENAI_API_KEY")

from haystack import Pipeline
from haystack.components.embedders import OpenAITextEmbedder
from haystack.utils import Secret
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator

class RetrieveDocuments:
    def __init__(self, doc_store, open_ai_key):
        # Initialize components
        text_embedder = OpenAITextEmbedder(api_key=Secret.from_token(open_ai_key))
        retriever = InMemoryEmbeddingRetriever(document_store=doc_store)
        reader = ExtractiveReader()
        reader.warm_up()
        # Build the pipeline
        self.query_pipeline = Pipeline()
        self.query_pipeline.add_component("embedder",text_embedder)
        self.query_pipeline.add_component("retriever", retriever)
        self.query_pipeline.add_component("reader", reader)

        # Connect components
        self.query_pipeline.connect("embedder.embedding", "retriever.query_embedding")
        self.query_pipeline.connect("retriever.documents", "reader.documents") 

    def run(self, query, symbols):
    
        logger.info(f"Running query pipeline with query: {query}")
        self.query_pipeline.draw("query_pipeline.png")
        # Pass query through the pipeline
        response = self.query_pipeline.run(
            data={"embedder": {"text": query}, 
                  "retriever": {"top_k": 3}, 
                  "reader": {"query": query, "top_k": 2}}
        )
        logger.info(f"Response: {response}")
        return response #["llm"]["replies"][0]


# load_dotenv(".env")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# document_store = InMemoryDocumentStore()
# query_pipeline = RetrieveDocuments(doc_store=document_store, open_ai_key=OPENAI_API_KEY)


# # Running the pipeline
# question = "Tell me about what you know"
# response = query_pipeline.run(question, "AAPL")

