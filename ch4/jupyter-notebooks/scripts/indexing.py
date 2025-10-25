import os
from getpass import getpass
import pandas as pd
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(".env")

# Import core Haystack classes
from haystack import Pipeline, Document
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.writers import DocumentWriter
from haystack.components.joiners import DocumentJoiner

# Import components for data fetching and conversion
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import (
    PyPDFToDocument,
    TextFileToDocument,
    HTMLToDocument,
)
from haystack.components.routers import FileTypeRouter

# Import components for preprocessing
from haystack.components.preprocessors import (
    DocumentCleaner,
    DocumentSplitter,
    CSVDocumentCleaner,
    CSVDocumentSplitter
)

# Import components for embedding
from haystack.components.embedders import SentenceTransformersDocumentEmbedder

# Assumes dummy data creation script has been run

from .dummy_data import text_file_path, pdf_file_path, csv_file_path

# Define a sample URL to fetch
web_url = "https://haystack.deepset.ai/blog/haystack-2-release"

# --- 2. Initialize Core Components ---

# DocumentStore: For this example, we use an in-memory store.
# For production, you would use a persistent vector database like Qdrant, Pinecone, or Weaviate. [11, 12]
document_store = InMemoryDocumentStore()

# FileTypeRouter: Directs files to the correct converter based on their MIME type. 
file_type_router = FileTypeRouter(mime_types=["text/plain", "application/pdf", "text/html"])

# Converters: One for each file type we want to handle.
text_file_converter = TextFileToDocument()
pdf_converter = PyPDFToDocument()
html_converter = HTMLToDocument()

# LinkContentFetcher: Fetches content from URLs and returns it as ByteStream objects. 
link_fetcher = LinkContentFetcher()

# DocumentJoiner: Merges lists of Documents from different paths into one. 
document_joiner = DocumentJoiner()

# Preprocessors for Text Data:
# DocumentCleaner: Removes extra whitespace, etc. 
cleaner = DocumentCleaner()
# DocumentSplitter: Chunks documents into smaller pieces. 
text_splitter = DocumentSplitter(split_by="word", split_length=150, split_overlap=20)

# Preprocessors for Tabular Data (CSV):
# CSVDocumentCleaner: Removes empty rows and columns from CSV data. [16, 17]
csv_cleaner = CSVDocumentCleaner()
# CSVDocumentSplitter: Splits a large CSV into smaller tables or row-wise documents. 
# Here, we split each row into a separate Document.
csv_splitter = CSVDocumentSplitter(split_mode="row-wise")

# Embedder: Creates vector representations of the documents.
# It's crucial to use a model that aligns with the one you'll use for querying.
doc_embedder = SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")

# DocumentWriter: Writes the final documents to the DocumentStore.
writer = DocumentWriter(document_store)

# --- 3. Build the Indexing Pipeline ---

indexing_pipeline = Pipeline()

# Add all components to the pipeline with unique names
indexing_pipeline.add_component("link_fetcher", link_fetcher)
indexing_pipeline.add_component("html_converter", html_converter)
indexing_pipeline.add_component("file_type_router", file_type_router)
indexing_pipeline.add_component("text_file_converter", text_file_converter)
indexing_pipeline.add_component("pdf_converter", pdf_converter)
indexing_pipeline.add_component("document_joiner", document_joiner)
indexing_pipeline.add_component("cleaner", cleaner)
indexing_pipeline.add_component("text_splitter", text_splitter)
indexing_pipeline.add_component("doc_embedder", doc_embedder)
indexing_pipeline.add_component("writer", writer)

# Add CSV-specific components
# We'll create a separate pipeline for CSV processing for clarity, then integrate the concept.
# In a single large pipeline, you would route CSV files similarly.
# For this example, we'll process the CSV separately and add it to the store.

# --- 4. Connect the Pipeline Components ---

# Web data branch
indexing_pipeline.connect("link_fetcher.streams", "html_converter.sources")
indexing_pipeline.connect("html_converter.documents", "document_joiner.documents")

# Local file data branch
indexing_pipeline.connect("file_type_router.text/plain", "text_file_converter.sources")
indexing_pipeline.connect("file_type_router.application/pdf", "pdf_converter.sources")
indexing_pipeline.connect("text_file_converter.documents", "document_joiner.documents")
indexing_pipeline.connect("pdf_converter.documents", "document_joiner.documents")

# Main processing path after joining
indexing_pipeline.connect("document_joiner", "cleaner")
indexing_pipeline.connect("cleaner", "text_splitter")
indexing_pipeline.connect("text_splitter", "doc_embedder")
indexing_pipeline.connect("doc_embedder", "writer")

print("Running indexing pipeline for web and local files...")
# Note: The PDF path will be ignored if the file doesn't exist.
file_paths_to_process = [text_file_path]
if pdf_file_path.exists() and pdf_file_path.stat().st_size > 0:
    file_paths_to_process.append(pdf_file_path)
else:
    print(f"Skipping PDF file: {pdf_file_path}")

indexing_pipeline.run({
    "link_fetcher": {"urls": [web_url]},
    "file_type_router": {"sources": file_paths_to_process}
})

