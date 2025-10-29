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
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore

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

# DocumentStore:
document_store = InMemoryDocumentStore()

# FileTypeRouter: Directs files to the correct converter based on their MIME type.
file_type_router = FileTypeRouter(mime_types=["text/plain", "application/pdf", "text/html", "text/csv"])

# Converters: One for each file type we want to handle.
text_converter = TextFileToDocument()
pdf_converter = PyPDFToDocument()
html_converter = HTMLToDocument()
# Added a dedicated converter instance for CSV files.
# It's also a TextFileToDocument, as it just needs to read the file's content.
csv_converter = TextFileToDocument()


# LinkContentFetcher: Fetches content from URLs.
link_fetcher = LinkContentFetcher()

# DocumentJoiners:
unstructured_doc_joiner = DocumentJoiner()
# This joiner will gather documents from *all* processing branches
# (the split text docs and the split csv docs) before embedding.
final_doc_joiner = DocumentJoiner()

# Preprocessors for Text Data:
text_cleaner = DocumentCleaner()
text_splitter = DocumentSplitter(split_by="word", split_length=150, split_overlap=20)

# Preprocessors for Tabular Data (CSV):
# These will now be part of the main pipeline.
csv_cleaner = CSVDocumentCleaner()
csv_splitter = CSVDocumentSplitter(split_mode="row-wise")

# Embedder:
doc_embedder = SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")

# DocumentWriter:
writer = DocumentWriter(document_store)


# --- 3. Build the Indexing Pipeline ---

indexing_pipeline = Pipeline()

# Add all components to the pipeline with unique names
indexing_pipeline.add_component("link_fetcher", link_fetcher)
indexing_pipeline.add_component("html_converter", html_converter)
indexing_pipeline.add_component("file_type_router", file_type_router)
indexing_pipeline.add_component("text_converter", text_converter)
indexing_pipeline.add_component("pdf_converter", pdf_converter)
indexing_pipeline.add_component("unstructured_doc_joiner", unstructured_doc_joiner)
indexing_pipeline.add_component("text_cleaner", text_cleaner)
indexing_pipeline.add_component("text_splitter", text_splitter)
indexing_pipeline.add_component("doc_embedder", doc_embedder)
indexing_pipeline.add_component("writer", writer)

# Add the CSV components to the pipeline
indexing_pipeline.add_component("csv_converter", csv_converter)
indexing_pipeline.add_component("csv_cleaner", csv_cleaner)
indexing_pipeline.add_component("csv_splitter", csv_splitter)
indexing_pipeline.add_component("final_doc_joiner", final_doc_joiner)

# --- 4. Connect the Pipeline Components ---

# --- Unstructured Data Branch (Web, TXT, PDF) ---
# Web data
indexing_pipeline.connect("link_fetcher.streams", "html_converter.sources")
indexing_pipeline.connect("html_converter.documents", "unstructured_doc_joiner.documents")

# Local file data (TXT, PDF)
indexing_pipeline.connect("file_type_router.text/plain", "text_converter.sources")
indexing_pipeline.connect("file_type_router.application/pdf", "pdf_converter.sources")
indexing_pipeline.connect("text_converter.documents", "unstructured_doc_joiner.documents")
indexing_pipeline.connect("pdf_converter.documents", "unstructured_doc_joiner.documents")

# Processing for unstructured data
indexing_pipeline.connect("unstructured_doc_joiner", "text_cleaner")
indexing_pipeline.connect("text_cleaner", "text_splitter")
# Connect the split *text* docs to the *final* joiner
indexing_pipeline.connect("text_splitter.documents", "final_doc_joiner.documents")


#  Structured Data Branch (CSV) ---
# Route CSV files to the csv_converter
indexing_pipeline.connect("file_type_router.text/csv", "csv_converter.sources")
# Process the CSV documents
indexing_pipeline.connect("csv_converter.documents", "csv_cleaner.documents")
indexing_pipeline.connect("csv_cleaner.documents", "csv_splitter.documents")
# Connect the split *csv* docs to the *final* joiner
indexing_pipeline.connect("csv_splitter.documents", "final_doc_joiner.documents")


# --- Main Processing Path (Embedding and Writing) ---
# The final_doc_joiner now receives documents from *both* branches
indexing_pipeline.connect("final_doc_joiner", "doc_embedder")
indexing_pipeline.connect("doc_embedder", "writer")


# --- 5. Run the Pipeline ---

print("Running unified indexing pipeline for web, local files, and CSV...")
# Note: The PDF path will be ignored if the file doesn't exist.
file_paths_to_process = [text_file_path]

if pdf_file_path.exists() and pdf_file_path.stat().st_size > 0:
    file_paths_to_process.append(pdf_file_path)
else:
    print(f"Skipping PDF file: {pdf_file_path}")

file_paths_to_process.append(csv_file_path)


indexing_pipeline.run({
    "link_fetcher": {"urls": [web_url]},
    "file_type_router": {"sources": file_paths_to_process}
})
