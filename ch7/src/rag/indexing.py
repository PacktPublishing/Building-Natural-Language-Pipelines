"""Document indexing pipeline for the Hybrid RAG system."""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from dotenv import load_dotenv

# Try loading .env from parent if present (local dev). In Docker the env vars are passed directly.
load_dotenv(".env")

# Import core Haystack classes
from haystack import Pipeline, super_component
from haystack.document_stores.types import DuplicatePolicy
from haystack.components.writers import DocumentWriter
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack.utils import Secret
from haystack.components.joiners import DocumentJoiner

# Import components for embedding
from haystack.components.embedders import OpenAIDocumentEmbedder
from haystack_integrations.components.embedders.fastembed import FastembedSparseDocumentEmbedder

# Import components for data fetching and conversion
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import (
    PyPDFToDocument,
    HTMLToDocument,
)
from haystack.components.routers import FileTypeRouter
from haystack.components.preprocessors import DocumentSplitter, DocumentCleaner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@super_component
class IndexingPipelineSuperComponent:
    def __init__(self, 
                 document_store, 
                 embedder_model: str = "text-embedding-3-small",
                 openai_api_key: Optional[str] = None):
        """
        Initialize the Indexing Pipeline SuperComponent.
        
        Args:
            document_store: Qdrant document store
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
        doc_joiner = DocumentJoiner(sort_by_score=False)  # Joins documents from different branches without sorting by score

        # Input converters for each file type
        pdf_converter = PyPDFToDocument()
        html_converter = HTMLToDocument()  # For URL content
        html_file_converter = HTMLToDocument()  # For HTML files
        link_fetcher = LinkContentFetcher()

        # Document cleaner to clean up text
        cleaner = DocumentCleaner(remove_empty_lines=True,
                                   remove_extra_whitespaces=True)

        # Splitter for Text Data:
        splitter = DocumentSplitter(split_by='sentence',
                                            split_length=50,
                                            split_overlap=5,
                                            )
        
        

        # Embedders:
        doc_embedder = OpenAIDocumentEmbedder(
            api_key=Secret.from_token(self.openai_api_key), 
            model=self.embedder_model
        )
        
        sparse_doc_embedder = FastembedSparseDocumentEmbedder()

        # DocumentWriter:
        writer = DocumentWriter(document_store=document_store, policy=DuplicatePolicy.OVERWRITE)

        self.pipeline = Pipeline()

        # Add all components to the pipeline with unique names
        self.pipeline.add_component("link_fetcher", link_fetcher)
        self.pipeline.add_component("html_converter", html_converter)
        self.pipeline.add_component("html_file_converter", html_file_converter)
        self.pipeline.add_component("file_type_router", file_router)
        self.pipeline.add_component("pdf_converter", pdf_converter)
        self.pipeline.add_component("doc_joiner", doc_joiner)
        self.pipeline.add_component("cleaner", cleaner)
        self.pipeline.add_component("doc_splitter", splitter)
        self.pipeline.add_component("doc_embedder", doc_embedder)
        self.pipeline.add_component("sparse_doc_embedder", sparse_doc_embedder)
        self.pipeline.add_component("writer", writer)

        # --- 4. Connect the Pipeline Components ---

        # URL content branch
        self.pipeline.connect("link_fetcher.streams", "html_converter.sources")
        self.pipeline.connect("html_converter.documents", "doc_joiner.documents")

        # File type routing branches
        self.pipeline.connect("file_type_router.application/pdf", "pdf_converter.sources")
        self.pipeline.connect("pdf_converter.documents", "doc_joiner.documents")
        
        # HTML files from file router go to separate HTML converter
        self.pipeline.connect("file_type_router.text/html", "html_file_converter.sources")
        self.pipeline.connect("html_file_converter.documents", "doc_joiner.documents")

        # Main processing path
        self.pipeline.connect("doc_joiner", "cleaner")
        self.pipeline.connect("cleaner", "doc_splitter")
        self.pipeline.connect("doc_splitter", "doc_embedder")
        self.pipeline.connect("doc_embedder", "sparse_doc_embedder")
        self.pipeline.connect("sparse_doc_embedder", "writer")
        
        # Separate input mappings for URLs and files
        self.input_mapping = {
            "urls": ["link_fetcher.urls"],
            "sources": ["file_type_router.sources"]
        }

def run_indexing_pipeline(qdrant_path: str = None, 
                         qdrant_index: str = None,
                         openai_api_key: str = None,
                         embedder_model: str = "text-embedding-3-small",
                         urls: List[str] = None,
                         files: List[str] = None) -> Dict[str, Any]:
    """
    Run the complete indexing pipeline.
    
    Args:
        qdrant_path: Qdrant storage path
        qdrant_index: Index name
        openai_api_key: OpenAI API key
        embedder_model: OpenAI embedding model
        urls: URLs to index
        files: File paths to index
        
    Returns:
        Dictionary with indexing results
    """
    # Get configuration from environment if not provided
    qdrant_path = qdrant_path or os.getenv('QDRANT_PATH', './qdrant_storage')
    qdrant_index = qdrant_index or os.getenv('QDRANT_INDEX', 'documents')
    openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
    urls = urls or []
    files = files or []

    if not openai_api_key:
        raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    
    logger.info(f"Starting indexing pipeline...")
    logger.info(f"Qdrant path: {qdrant_path}")
    logger.info(f"Qdrant index: {qdrant_index}")
    logger.info(f"URLs to index: {len(urls)}")
    logger.info(f"Files to index: {len(files)}")

    try:
        # Initialize document store with on-disk storage and sparse embeddings support
        logger.info("Initializing Qdrant document store...")
        document_store = QdrantDocumentStore(
            path=qdrant_path,
            index=qdrant_index,
            embedding_dim=1536,  # text-embedding-3-small dimension
            recreate_index=False,
            use_sparse_embeddings=True  # Enable sparse embeddings for hybrid retrieval
        )
        
        # Create indexing pipeline
        logger.info("Creating indexing pipeline...")
        # Define sources: separate URLs and files
        

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
            "qdrant_path": qdrant_path,
            "qdrant_index": qdrant_index,
            "urls_processed": len(urls),
            "files_processed": len(files)
        }
        
    except Exception as e:
        logger.error(f"Indexing pipeline failed: {str(e)}")
        raise e


def main():
    """Main function to run indexing pipeline."""
    try:
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
        result = run_indexing_pipeline(urls=urls, files=files)
        print(f"✅ Indexing completed: {result}")
    except Exception as e:
        print(f"❌ Indexing failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()