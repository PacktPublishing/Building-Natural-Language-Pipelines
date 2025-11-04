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


from haystack.components.preprocessors import DocumentPreprocessor


@super_component
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
        self.pipeline.connect("doc_preprocessor", "doc_embedder")
        self.pipeline.connect("doc_embedder", "writer")
        
        # Separate input mappings for URLs and files
        self.input_mapping = {
            "urls": ["link_fetcher.urls"],
            "sources": ["file_type_router.sources"]
        }



if __name__ == "__main__":
    # Define sources: separate URLs and files
    pdf_file = Path("./data_for_indexing/howpeopleuseai.pdf")
    
    # URLs for web content
    urls = [
            "https://www.bbc.com/news/articles/c2l799gxjjpo",
            "https://www.brookings.edu/articles/how-artificial-intelligence-is-transforming-the-world/"
    ]
    
    # Files for local content  
    files = [pdf_file]

    # --- 2. Initialize Core Components ---
    # DocumentStore:
    document_store = ElasticsearchDocumentStore(hosts="http://localhost:9200")

    indexing_pipeline_sc = IndexingPipelineSuperComponent( 
        document_store=document_store,
        embedder_model="text-embedding-3-small",
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )

    # --- 5. Run the Pipeline ---

    print("Running indexing pipeline for PDF file and web URL...")

    # Check if PDF file exists
    if not pdf_file.exists():
        print(f"Error: PDF file not found at {pdf_file}")
        exit(1)

    # Run with separate inputs for URLs and files
    indexing_pipeline_sc.run(urls=urls, sources=files)

    print("Indexing completed successfully!")
