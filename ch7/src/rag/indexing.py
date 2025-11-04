"""Document indexing pipeline for the Hybrid RAG system."""

import os
from getpass import getpass
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from dotenv import load_dotenv
from transformers import pipeline

# Try loading .env from parent if present (local dev). In Docker the env vars are passed directly.
load_dotenv(".env")

# Import core Haystack classes
from haystack import Pipeline, super_component, component
from haystack.document_stores.types import DuplicatePolicy
from haystack.components.writers import DocumentWriter
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack.utils import Secret
from haystack.components.joiners import DocumentJoiner
from haystack.dataclasses import Document
from typing import List

# Import components for embedding
from haystack.components.embedders import OpenAIDocumentEmbedder

# Import components for data fetching and conversion
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import (
    PyPDFToDocument,
    HTMLToDocument,
)
from haystack.components.routers import FileTypeRouter
from haystack.components.preprocessors import DocumentPreprocessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


import os
from getpass import getpass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from transformers import pipeline

load_dotenv(".env")

# Import core Haystack classes
from haystack import Pipeline, super_component
from haystack.document_stores.types import DuplicatePolicy
from haystack.components.writers import DocumentWriter
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack.utils import Secret
from haystack.components.joiners import DocumentJoiner


# Import components for embedding
from haystack.components.embedders import OpenAIDocumentEmbedder

# Import components for data fetching and conversion
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import (
    PyPDFToDocument,
    HTMLToDocument,
)
from haystack.components.routers import FileTypeRouter


from haystack.components.preprocessors import DocumentPreprocessor, DocumentCleaner

# Import for custom component
from haystack import component
from haystack.dataclasses import Document
from typing import List


class IndexingPipelineSuperComponent:
    def __init__(self, 
                 document_store, 
                 embedder_model: str = "text-embedding-3-small",
                 openai_api_key: Optional[str] = None):
        """
        Initialize the Indexing Pipeline SuperComponent.
        
        Args:
            document_store: Elasticsearch document store
            embedder_model (str): OpenAI embedding model name. Defaults to "text-embedding-3-small".
            openai_api_key (Optional[str]): OpenAI API key. If None, will use environment variable.
        """
        self.embedder_model = embedder_model
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")
        
        self._build_pipeline(document_store)
    
    def _build_pipeline(self, document_store):
        """Build the indexing pipeline with initialized components."""
        
        # Core routing and joining components  
        file_router = FileTypeRouter(mime_types=["text/plain", "application/pdf", "text/html"])
        doc_joiner = DocumentJoiner()  # Joins documents from different branches

        # Input converters for each file type
        pdf_converter = PyPDFToDocument()
        html_converter = HTMLToDocument()  
        link_fetcher = LinkContentFetcher()


        # Preprocessors for Text Data:
        preprocessor = DocumentPreprocessor(split_by='sentence',
                                            split_length=50,
                                            split_overlap=5,
                                            remove_empty_lines = True,
                                            remove_extra_whitespaces = True,
                                            )
        
        # Document cleaner to clean up text
        cleaner = DocumentCleaner()

        # Embedder:
        doc_embedder = OpenAIDocumentEmbedder(
            api_key=Secret.from_token(self.openai_api_key), 
            model=self.embedder_model
        )

        # DocumentWriter:
        writer = DocumentWriter(document_store=document_store, policy=DuplicatePolicy.OVERWRITE)

        self.pipeline = Pipeline()

        # Add all components to the pipeline with unique names
        self.pipeline.add_component("link_fetcher", link_fetcher)
        self.pipeline.add_component("html_converter", html_converter)
        self.pipeline.add_component("file_type_router", file_router)
        self.pipeline.add_component("pdf_converter", pdf_converter)
        self.pipeline.add_component("doc_joiner", doc_joiner)
        self.pipeline.add_component("doc_preprocessor", preprocessor)
        self.pipeline.add_component("cleaner", cleaner)
        self.pipeline.add_component("doc_embedder", doc_embedder)
        self.pipeline.add_component("writer", writer)

        # --- 4. Connect the Pipeline Components ---

        # Web data branch
        self.pipeline.connect("link_fetcher.streams", "html_converter.sources")
        self.pipeline.connect("html_converter.documents", "doc_joiner.documents")

        # PDF file branch
        self.pipeline.connect("file_type_router.application/pdf", "pdf_converter.sources")
        self.pipeline.connect("pdf_converter.documents", "doc_joiner.documents")

        # Main processing path
        self.pipeline.connect("doc_joiner", "doc_preprocessor")
        self.pipeline.connect("doc_preprocessor", "cleaner")
        self.pipeline.connect("cleaner", "doc_embedder")
        self.pipeline.connect("doc_embedder", "writer")
        
        # Pipeline is ready to use
    
    def run(self, urls: Optional[List[str]] = None, sources: Optional[List[str]] = None):
        """
        Run the indexing pipeline with URLs and/or file sources.
        
        Args:
            urls: List of URLs to fetch and index
            sources: List of file paths to index
            
        Returns:
            Pipeline execution result
        """
        if not urls and not sources:
            raise ValueError("At least one of 'urls' or 'sources' must be provided")
        
        inputs = {}
        
        if urls:
            inputs["link_fetcher"] = {"urls": urls}
            
        if sources:
            inputs["file_type_router"] = {"sources": sources}
        
        return self.pipeline.run(inputs)


def run_indexing_pipeline(elasticsearch_host: str = None, 
                         elasticsearch_index: str = None,
                         openai_api_key: str = None,
                         embedder_model: str = "text-embedding-3-small",
                         urls: List[str] = None) -> Dict[str, Any]:
    """
    Run the complete indexing pipeline.
    
    Args:
        elasticsearch_host: Elasticsearch host URL
        elasticsearch_index: Index name
        openai_api_key: OpenAI API key
        embedder_model: OpenAI embedding model
        urls: URLs to index
        
    Returns:
        Dictionary with indexing results
    """
    # Get configuration from environment if not provided
    elasticsearch_host = elasticsearch_host or os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')
    elasticsearch_index = elasticsearch_index or os.getenv('ELASTICSEARCH_INDEX', 'documents')
    openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
    urls = urls or get_sample_urls()
    
    if not openai_api_key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    
    logger.info(f"Starting indexing pipeline...")
    logger.info(f"Elasticsearch host: {elasticsearch_host}")
    logger.info(f"Elasticsearch index: {elasticsearch_index}")
    logger.info(f"URLs to index: {len(urls)}")
    
    try:
        # Initialize document store
        logger.info("Initializing Elasticsearch document store...")
        document_store = ElasticsearchDocumentStore(
            hosts=elasticsearch_host,
            index=elasticsearch_index
        )
        
        # Create indexing pipeline
        logger.info("Creating indexing pipeline...")
        # Define sources: separate URLs and files
        logger.info("Defining data sources for indexing...")
        pdf_file = Path("./data_for_indexing/howpeopleuseai.pdf")
        
        if not pdf_file.exists():
            raise FileNotFoundError(f"Sample PDF file not found at {pdf_file}. Please ensure the file exists.")
        
        # URLs for web content
        urls = [
                "https://www.bbc.com/news/articles/c2l799gxjjpo",
                "https://www.brookings.edu/articles/how-artificial-intelligence-is-transforming-the-world/"
        ]
        
        # Files for local content  
        files = [pdf_file]

        indexing_pipeline_sc_small = IndexingPipelineSuperComponent( 
            document_store=document_store,
            embedder_model="text-embedding-3-small",
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )
     
        # Run pipeline
        logger.info("Running indexing pipeline...")
        result = indexing_pipeline_sc_small.run(urls=urls, sources=files)
        
        
        logger.info(f"Indexing completed successfully!")
        
        return {
            "status": "success",
            "result": result,
            "elasticsearch_host": elasticsearch_host,
            "elasticsearch_index": elasticsearch_index,
            "urls_processed": len(urls)
        }
        
    except Exception as e:
        logger.error(f"Indexing pipeline failed: {str(e)}")
        raise e


def main():
    """Main function to run indexing pipeline."""
    try:
        result = run_indexing_pipeline()
        print(f"✅ Indexing completed: {result}")
    except Exception as e:
        print(f"❌ Indexing failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()