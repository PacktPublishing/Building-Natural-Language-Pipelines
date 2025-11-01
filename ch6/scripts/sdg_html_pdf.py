import os
from dotenv import load_dotenv
from haystack import Pipeline
from haystack.components.converters import PyPDFToDocument, HTMLToDocument
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.routers import FileTypeRouter
from haystack.components.joiners import DocumentJoiner
from haystack.components.preprocessors import (
    DocumentCleaner,
    DocumentSplitter)
from pathlib import Path
from scripts.knowledge_graph_component import KnowledgeGraphGenerator,\
                                                DocumentToLangChainConverter
from scripts.synthetic_test_components import SyntheticTestGenerator,\
                                                TestDatasetSaver

# Load environment variables
load_dotenv(".env")

# Initialize pipeline
pipeline = Pipeline()

# Core routing and joining components  
file_router = FileTypeRouter(mime_types=["text/plain", "application/pdf", "text/html"])
doc_joiner = DocumentJoiner()  # Joins documents from different branches

# Input converters for each file type
pdf_converter = PyPDFToDocument()
html_converter = HTMLToDocument()  
link_fetcher = LinkContentFetcher()

# Shared processing components
doc_cleaner = DocumentCleaner(
    remove_empty_lines=True, 
    remove_extra_whitespaces=True
)
doc_splitter = DocumentSplitter(split_by="sentence", split_length=50, split_overlap=5)
doc_converter = DocumentToLangChainConverter()
kg_generator = KnowledgeGraphGenerator(apply_transforms=False)
test_generator = SyntheticTestGenerator(
    testset_size=15,  # Larger test set for multiple sources
    llm_model="gpt-4o-mini",
    query_distribution=[
        ("single_hop", 0.3),
        ("multi_hop_specific", 0.3), 
        ("multi_hop_abstract", 0.4)
    ]
)
test_saver = TestDatasetSaver("data_for_eval/synthetic_tests_advanced_branching.csv")

# Add all components to pipeline
pipeline.add_component("file_router", file_router)
pipeline.add_component("link_fetcher", link_fetcher)
pipeline.add_component("pdf_converter", pdf_converter) 
pipeline.add_component("html_converter", html_converter)
pipeline.add_component("doc_joiner", doc_joiner)
pipeline.add_component("doc_cleaner", doc_cleaner)
pipeline.add_component("doc_splitter", doc_splitter)
pipeline.add_component("doc_converter", doc_converter)
pipeline.add_component("kg_generator", kg_generator)
pipeline.add_component("test_generator", test_generator)
pipeline.add_component("test_saver", test_saver)

# Connect file routing branches
pipeline.connect("file_router.application/pdf", "pdf_converter.sources") 
pipeline.connect("link_fetcher.streams", "html_converter.sources")

# Connect converters to joiner
pipeline.connect("pdf_converter.documents", "doc_joiner.documents")
pipeline.connect("html_converter.documents", "doc_joiner.documents")

# Connect main processing path
pipeline.connect("doc_joiner.documents", "doc_cleaner.documents")
pipeline.connect("doc_cleaner.documents", "doc_splitter.documents")
pipeline.connect("doc_splitter.documents", "doc_converter.documents")
pipeline.connect("doc_converter.langchain_documents", "kg_generator.documents")
pipeline.connect("kg_generator.knowledge_graph", "test_generator.knowledge_graph")
pipeline.connect("doc_converter.langchain_documents", "test_generator.documents")
pipeline.connect("test_generator.testset", "test_saver.testset")

pdf_file = Path("./data_for_indexing/howpeopleuseai.pdf")
web_url = "https://haystack.deepset.ai/blog/haystack-2-release"

# Run pipeline with both input types
result = pipeline.run({
    "file_router": {"sources": [pdf_file]},  # PDF input through FileTypeRouter
    "link_fetcher": {"urls": [web_url]}      # Web input through LinkContentFetcher
})
    
