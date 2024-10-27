from haystack.components.preprocessors import DocumentCleaner
from haystack.components.embedders import OpenAITextEmbedder, OpenAIDocumentEmbedder
from haystack import Pipeline
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy
from haystack.utils import Secret
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore

from haystack import component, Document
from typing import Any, Dict, List, Union
from haystack.dataclasses import ByteStream

import wandb
from dotenv import load_dotenv
import os
import time
import json
import logging

import re
from bs4 import BeautifulSoup
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(".env")

# Initialize Weights and Biases
os.environ["WANDB_API_KEY"] = os.getenv("WANDB_API_KEY")
wandb.init(project="haystack-indexing", config={"task": "Indexing Pipeline"})

# Load OpenAI API key
open_ai_key = os.environ.get("OPENAI_API_KEY")

# Initialize ElasticsearchDocumentStore and embedder
document_store = ElasticsearchDocumentStore(hosts="http://localhost:9200")
text_embedder = OpenAITextEmbedder(api_key=Secret.from_token(open_ai_key))

# Load dataset and log dataset metadata
with open("news_out.jsonl", 'r') as file:
    data = [json.loads(line) for line in file]
wandb.config.update({"dataset_size": len(data)})

def read_jsonl_file(file_path):
    """
    Reads a JSONL (JSON Lines) file and returns a list of dictionaries representing each valid JSON object.
    Lines with JSON decoding errors are skipped.
    
    :param file_path: The path to the JSONL file.
    :return: A list of dictionaries, each representing a parsed JSON object.
    """
    data = []
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                try:
                    # Attempt to load the JSON data from the current line
                    json_data = json.loads(line)
                    data.append(json_data)
                except json.JSONDecodeError as e:
                    # Log an error message for any lines that can't be decoded
                    logger.error(f"Error decoding JSON on line: {line[:30]}... - {e}")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
    
    return data

        
@component
class BenzingaNews:
    
    @component.output_types(documents=List[Document])
    def run(self, sources: Dict[str, Any]) -> None:
        logger.info("Starting BenzingaNews.run with sources")
        documents = []
        try:
            for source in sources:
                logger.debug(f"Processing source: {source.get('headline', 'Unknown headline')}")
                for key in source:
                    if isinstance(source[key], str):
                        source[key] = self.clean_text(source[key])
                
                if source['content'] == "":
                    logger.warning(f"Skipping source due to empty content: {source.get('headline', 'Unknown headline')}")
                    continue

                # Create a Document with the cleaned content and metadata
                content = source['content']
                document = Document(content=content, meta=source)
                documents.append(document)
            
            logger.info(f"Successfully processed {len(documents)} documents.")
        
        except Exception as e:
            logger.error(f"Error during BenzingaNews.run: {e}")
        
        return {"documents": documents}
               
    def clean_text(self, text):
        logger.debug("Cleaning text content.")
        try:
            # Remove HTML tags using BeautifulSoup
            soup = BeautifulSoup(text, "html.parser")
            text = soup.get_text()
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            logger.debug("Text cleaned successfully.")
        except Exception as e:
            logger.error(f"Error during text cleaning: {e}")
            raise
        return text


@component
class BenzingaEmbeder:
    
    def __init__(self):
        logger.info("Initializing BenzingaEmbeder pipeline.")
        try:
            get_news = BenzingaNews()
            document_store = ElasticsearchDocumentStore(embedding_similarity_function="cosine", hosts="http://localhost:9200")
            document_cleaner = DocumentCleaner(
                                remove_empty_lines=True,
                                remove_extra_whitespaces=True,
                                remove_repeated_substrings=False
                            )
            document_splitter = DocumentSplitter(split_by="passage", split_length=5)
            document_writer = DocumentWriter(document_store=document_store,
                                             policy=DuplicatePolicy.OVERWRITE)
            embedding = OpenAIDocumentEmbedder(api_key=Secret.from_token(open_ai_key))

            self.pipeline = Pipeline()
            self.pipeline.add_component("get_news", get_news)
            self.pipeline.add_component("document_cleaner", document_cleaner)
            self.pipeline.add_component("document_splitter", document_splitter)
            self.pipeline.add_component("embedding", embedding)
            self.pipeline.add_component("document_writer", document_writer)

            self.pipeline.connect("get_news", "document_cleaner")
            self.pipeline.connect("document_cleaner", "document_splitter")
            self.pipeline.connect("document_splitter", "embedding")
            self.pipeline.connect("embedding", "document_writer")

            logger.info("Pipeline initialized successfully.")
        except Exception as e:
            logger.error(f"Error during BenzingaEmbeder initialization: {e}")
            raise

    @component.output_types(documents=List[Document])
    def run(self, event: List[Union[str, Path, ByteStream]]):
        logger.info(f"Running BenzingaEmbeder with event: {event}")
        try:
            documents = self.pipeline.run({"get_news": {"sources": [event]}})
            self.pipeline.draw("benzinga_pipeline.png")
            logger.info("Pipeline executed successfully, drawing pipeline graph.")
            return documents
        except Exception as e:
            logger.error(f"Error during pipeline execution: {e}")
            raise
    
if __name__ == "__main__":
    document_embedder = BenzingaEmbeder()
    data = read_jsonl_file("./news_out.jsonl")

    for ite in data:
        try:
            start_time = time.time()
            documents = document_embedder.run(ite)
            end_time = time.time()
            # Log individual document metrics
            wandb.log({
                "embedding_time": end_time - start_time,
                "embedding_token_usage": documents['embedding']['meta']['usage']['total_tokens'],
            })
            
            print(documents['embedding']['meta']['usage']['total_tokens'])
        except Exception as e:
            logger.error(f"Error during document embedding: {e}")
            wandb.log({"embedding_status": 0})
    wandb.finish()
