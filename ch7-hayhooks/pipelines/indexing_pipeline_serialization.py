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
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize document store
document_store = ElasticsearchDocumentStore(
    hosts=os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200"),
    index="small_embeddings"
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
pipeline.connect("doc_embedder", "writer")

with open("./pipelines/indexing/indexing.yml", "w") as file:
  pipeline.dump(file)