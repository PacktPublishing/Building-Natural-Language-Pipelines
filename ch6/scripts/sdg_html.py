
import os
from dotenv import load_dotenv
from haystack import Pipeline
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import HTMLToDocument
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

# Create web content processing components
fetcher = LinkContentFetcher()
converter = HTMLToDocument()
doc_cleaner = DocumentCleaner(
    remove_empty_lines=True,
    remove_extra_whitespaces=True,
)
doc_splitter = DocumentSplitter(split_by="sentence",
                                split_length=100,
                                split_overlap=5)
doc_converter = DocumentToLangChainConverter()
kg_generator = KnowledgeGraphGenerator(apply_transforms=True)
test_generator = SyntheticTestGenerator(
            testset_size=10,  
            llm_model="gpt-4o-mini",
            query_distribution=[
                ("single_hop", 0.25), 
                ("multi_hop_specific", 0.25),
                ("multi_hop_abstract", 0.5)
            ]
        )
test_saver = TestDatasetSaver("data_for_eval/synthetic_tests_10_from_web.csv")

# Create pipeline
pipeline = Pipeline()
pipeline.add_component("fetcher", fetcher)
pipeline.add_component("converter", converter)
pipeline.add_component("doc_cleaner", doc_cleaner)
pipeline.add_component("doc_splitter", doc_splitter)
pipeline.add_component("doc_converter", doc_converter)
pipeline.add_component("kg_generator", kg_generator)
pipeline.add_component("test_generator", test_generator)
pipeline.add_component("test_saver", test_saver)

# Connect components in sequence
pipeline.connect("fetcher.streams", "converter.sources")
pipeline.connect("converter.documents", "doc_cleaner.documents")
pipeline.connect("doc_cleaner.documents", "doc_splitter.documents")
pipeline.connect("doc_splitter.documents", "doc_converter.documents")
pipeline.connect("doc_converter.langchain_documents", "kg_generator.documents")
pipeline.connect("kg_generator.knowledge_graph", "test_generator.knowledge_graph")
pipeline.connect("doc_converter.langchain_documents", "test_generator.documents")
pipeline.connect("test_generator.testset", "test_saver.testset")

web_url = "https://haystack.deepset.ai/blog/haystack-2-release"

result = pipeline.run({
    "fetcher": {"urls": [web_url]}
})

