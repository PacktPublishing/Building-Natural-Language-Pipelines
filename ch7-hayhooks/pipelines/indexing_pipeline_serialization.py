from haystack import Pipeline
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import HTMLToDocument, PyPDFToDocument
from haystack.components.routers import FileTypeRouter
from haystack.components.joiners import DocumentJoiner
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.embedders import OpenAIDocumentEmbedder
from haystack.components.writers import DocumentWriter
from haystack.utils import Secret
from haystack.document_stores.types import DuplicatePolicy
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.embedders.fastembed import FastembedSparseDocumentEmbedder
import os
from dotenv import load_dotenv
import yaml
load_dotenv()

# Initialize document store with on-disk storage and sparse embeddings support
document_store = QdrantDocumentStore(
    path="./qdrant_storage",
    index="documents",
    embedding_dim=1536,  # text-embedding-3-small dimension
    recreate_index=False,
    use_sparse_embeddings=True  # Enable sparse embeddings for hybrid retrieval
)

   
pipeline = Pipeline()
    
# Core components
file_router = FileTypeRouter(mime_types=["text/plain", "application/pdf", "text/html"])
doc_joiner = DocumentJoiner(sort_by_score=False)
pdf_converter = PyPDFToDocument()
html_converter = HTMLToDocument()  # For URL content
html_file_converter = HTMLToDocument()  # For HTML files
link_fetcher = LinkContentFetcher()
cleaner = DocumentCleaner(
    remove_empty_lines=True,
    remove_extra_whitespaces=True
)
splitter = DocumentSplitter(
    split_by='sentence',
    split_length=50,
    split_overlap=5
)
doc_embedder = OpenAIDocumentEmbedder(
    api_key=Secret.from_env_var("OPENAI_API_KEY"),
    model="text-embedding-3-small"
)
sparse_doc_embedder = FastembedSparseDocumentEmbedder()
writer = DocumentWriter(
    document_store=document_store,
    policy=DuplicatePolicy.OVERWRITE
)

# Add components
pipeline.add_component("link_fetcher", link_fetcher)
pipeline.add_component("html_converter", html_converter)
pipeline.add_component("html_file_converter", html_file_converter)
pipeline.add_component("file_type_router", file_router)
pipeline.add_component("pdf_converter", pdf_converter)
pipeline.add_component("doc_joiner", doc_joiner)
pipeline.add_component("cleaner", cleaner)
pipeline.add_component("doc_splitter", splitter)
pipeline.add_component("doc_embedder", doc_embedder)
pipeline.add_component("sparse_doc_embedder", sparse_doc_embedder)
pipeline.add_component("writer", writer)

# Connect components
# URL content branch
pipeline.connect("link_fetcher.streams", "html_converter.sources")
pipeline.connect("html_converter.documents", "doc_joiner.documents")

# File type routing branches
pipeline.connect("file_type_router.application/pdf", "pdf_converter.sources")
pipeline.connect("pdf_converter.documents", "doc_joiner.documents")

# HTML files from file router go to separate HTML converter
pipeline.connect("file_type_router.text/html", "html_file_converter.sources")
pipeline.connect("html_file_converter.documents", "doc_joiner.documents")

# Main processing path
pipeline.connect("doc_joiner", "cleaner")
pipeline.connect("cleaner", "doc_splitter")
pipeline.connect("doc_splitter", "doc_embedder")
pipeline.connect("doc_embedder", "sparse_doc_embedder")
pipeline.connect("sparse_doc_embedder", "writer")


output_path = "./pipelines/indexing/indexing.yml"
# Dump the pipeline
with open(output_path, "w") as file:
    pipeline.dump(file)
    
print(f"Pipeline serialized to {output_path}")