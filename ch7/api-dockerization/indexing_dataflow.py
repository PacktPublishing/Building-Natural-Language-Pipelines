from bytewax.dataflow import Dataflow
from bytewax import operators as op
from bytewax.connectors.files import FileSource
from bytewax.connectors.stdio import StdOutSink

from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.embedders import OpenAIDocumentEmbedder
from haystack import Pipeline
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy
from haystack.utils import Secret


from haystack import component, Document
from typing import Any, Dict, List, Union
from haystack.dataclasses import ByteStream

import json
from dotenv import load_dotenv
import os

import re
from bs4 import BeautifulSoup
from pathlib import Path

import logging



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_deserialize(data):
        """
        Safely deserialize JSON data, handling various formats.
        
        :param data: JSON data to deserialize.
        :return: Deserialized data or None if an error occurs.
        """
        try:
            parsed_data = json.loads(data)
            if isinstance(parsed_data, list):
                if len(parsed_data) == 2 and (parsed_data[0] is None or isinstance(parsed_data[0], str)):
                    event = parsed_data[1]
                else:
                    logger.info(f"Skipping unexpected list format: {data}")
                    return None
            elif isinstance(parsed_data, dict):
                event = parsed_data
            else:
                logger.info(f"Skipping unexpected data type: {data}")
                return None
            
            if 'link' in event:
                event['url'] = event.pop('link')
            
            if "url" in event:
                return event
            else:
                logger.info(f"Missing 'url' key in data: {data}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error ({e}) for data: {data}")
            return None
        except Exception as e:
            logger.error(f"Error processing data ({e}): {data}")
            return None

        
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
                document = Document(content=content, meta={"symbols": source.get("symbols", ""), **source})
                documents.append(document)
                logger.info(f"DOCUMENT {document}")
            
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
class BenzingaEmbedder:
    
    def __init__(self, document_store, open_ai_key):
        logger.info("Initializing BenzingaEmbeder pipeline.")
        try:
            get_news = BenzingaNews()
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
        

def filter_data(event, symbol):
    """Filter the data based on the symbol."""
    return event and "symbols" in event and symbol in event["symbols"]
    
def run_pipeline_with_symbol(symbol, document_store, open_ai_key):
    embed_benzinga = BenzingaEmbedder(document_store, open_ai_key)
    
    def process_event(event):
        """Wrapper to handle the processing of each event."""
        if event:
            document = embed_benzinga.run(event)
            return document
        return None
    
    flow = Dataflow("rag-pipeline")
    input_data = op.input("input", flow, FileSource("news_out.jsonl"))
    deserialize_data = op.map("deserialize", input_data, safe_deserialize)
    
    # Use a lambda to pass the symbol to the filter_data function
    filtered_data = op.filter("filter_data", deserialize_data, lambda event: filter_data(event, symbol))
    embed_data = op.map("embed_data", filtered_data, process_event)
    op.output("output", embed_data, StdOutSink())
    return flow
