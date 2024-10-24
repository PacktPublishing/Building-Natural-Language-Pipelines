from haystack.components.preprocessors import DocumentCleaner
from haystack.components.embedders import OpenAIDocumentEmbedder
from haystack import Pipeline
from haystack.components.embedders import OpenAIDocumentEmbedder
from haystack.components.preprocessors import DocumentCleaner
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.utils import Secret
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore


from haystack import component, Document
from typing import Any, Dict, List, Optional, Union
from haystack.dataclasses import ByteStream

import json
from dotenv import load_dotenv
import os

import re
from bs4 import BeautifulSoup
from pathlib import Path

import logging

load_dotenv(".env")
open_ai_key = os.environ.get("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import json

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
             
        documents = []
        for source in sources:
        
            for key in source:
                if type(source[key]) == str:
                    source[key] = self.clean_text(source[key])
                    
            if source['content'] == "":
                continue

            #drop content from source dictionary
            content = source['content']
            document = Document(content=content, meta=source) 
            
            documents.append(document)
         
        return {"documents": documents}
               
    def clean_text(self, text):
        # Remove HTML tags using BeautifulSoup
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
@component
class BenzingaEmbeder:
    
    def __init__(self):
        get_news = BenzingaNews()
        document_store = ElasticsearchDocumentStore(embedding_similarity_function="cosine", hosts = "http://localhost:9200")
        document_cleaner = DocumentCleaner(
                            remove_empty_lines=True,
                            remove_extra_whitespaces=True,
                            remove_repeated_substrings=False
                        )
        document_splitter = DocumentSplitter(split_by="passage", split_length=5)
        document_writer = DocumentWriter(document_store=document_store,
                                        policy = DuplicatePolicy.OVERWRITE)
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
        
        
    @component.output_types(documents=List[Document])
    def run(self, event: List[Union[str, Path, ByteStream]]):
        
        documents = self.pipeline.run({"get_news": {"sources": [event]}})
        
        self.pipeline.draw("benzinga_pipeline.png")
        return documents
    

document_embedder = BenzingaEmbeder()
data = read_jsonl_file("./news_out.jsonl")


for ite in data:
    print(document_embedder.run(ite))
