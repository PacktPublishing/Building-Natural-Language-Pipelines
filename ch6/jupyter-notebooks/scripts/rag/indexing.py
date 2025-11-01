import os
from getpass import getpass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(".env")

# Import core Haystack classes
from haystack import Pipeline
from haystack.document_stores.types import DuplicatePolicy
from haystack.components.writers import DocumentWriter
from haystack.components.joiners import DocumentJoiner
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore

# Import components for data fetching and conversion
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import (
    PyPDFToDocument,
    HTMLToDocument,
)
from haystack.components.routers import FileTypeRouter

# Import components for preprocessing
from haystack.components.preprocessors import (
    DocumentCleaner,
    DocumentSplitter,
)

# Import components for embedding
from haystack.components.embedders import SentenceTransformersDocumentEmbedder

# Define sources: only PDF file and web URL
pdf_file = Path("./data_for_indexing/howpeopleuseai.pdf")
web_urls = ["https://www.bbc.com/news/articles/c2l799gxjjpo",
            "https://www.brookings.edu/articles/how-artificial-intelligence-is-transforming-the-world/"
            ]

# --- 2. Initialize Core Components ---

# DocumentStore:
document_store = ElasticsearchDocumentStore(hosts="http://localhost:9200")

# FileTypeRouter: Directs files to the correct converter based on their MIME type.
file_type_router = FileTypeRouter(mime_types=["application/pdf", "text/html"])

# Converters: Only PDF and HTML converters needed
pdf_converter = PyPDFToDocument()
html_converter = HTMLToDocument()


# LinkContentFetcher: Fetches content from URLs.
link_fetcher = LinkContentFetcher()

# DocumentJoiner: Will gather documents from both PDF and web sources
doc_joiner = DocumentJoiner()

# Preprocessors: For cleaning and splitting documents
doc_cleaner = DocumentCleaner()
doc_splitter = DocumentSplitter(split_by="sentence", split_length=150, split_overlap=20)

# Embedder:
doc_embedder = SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")

# DocumentWriter:
writer = DocumentWriter(document_store, policy=DuplicatePolicy.OVERWRITE)


# --- 3. Build the Indexing Pipeline ---

indexing_pipeline = Pipeline()

# Add all components to the pipeline with unique names
indexing_pipeline.add_component("link_fetcher", link_fetcher)
indexing_pipeline.add_component("html_converter", html_converter)
indexing_pipeline.add_component("file_type_router", file_type_router)
indexing_pipeline.add_component("pdf_converter", pdf_converter)
indexing_pipeline.add_component("doc_joiner", doc_joiner)
indexing_pipeline.add_component("doc_cleaner", doc_cleaner)
indexing_pipeline.add_component("doc_splitter", doc_splitter)
indexing_pipeline.add_component("doc_embedder", doc_embedder)
indexing_pipeline.add_component("writer", writer)

# --- 4. Connect the Pipeline Components ---

# Web data branch
indexing_pipeline.connect("link_fetcher.streams", "html_converter.sources")
indexing_pipeline.connect("html_converter.documents", "doc_joiner.documents")

# PDF file branch
indexing_pipeline.connect("file_type_router.application/pdf", "pdf_converter.sources")
indexing_pipeline.connect("pdf_converter.documents", "doc_joiner.documents")

# Main processing path
indexing_pipeline.connect("doc_joiner", "doc_cleaner")
indexing_pipeline.connect("doc_cleaner", "doc_splitter")
indexing_pipeline.connect("doc_splitter", "doc_embedder")
indexing_pipeline.connect("doc_embedder", "writer")


# --- 5. Run the Pipeline ---

print("Running indexing pipeline for PDF file and web URL...")

# Check if PDF file exists
if not pdf_file.exists():
    print(f"Error: PDF file not found at {pdf_file}")
    exit(1)

print(f"Processing PDF: {pdf_file}")
print(f"Processing web URL: {web_urls}")

indexing_pipeline.run({
    "link_fetcher": {"urls": web_urls},
    "file_type_router": {"sources": [pdf_file]}
})

print("Indexing completed successfully!")
