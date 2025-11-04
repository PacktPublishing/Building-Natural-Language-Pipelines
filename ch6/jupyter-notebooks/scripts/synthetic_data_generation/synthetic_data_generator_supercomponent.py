import os
from dotenv import load_dotenv
from haystack import Pipeline, super_component
from haystack.components.preprocessors import DocumentPreprocessor
# Import components for data fetching and conversion
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import (
    PyPDFToDocument,
    HTMLToDocument,
)
from haystack.components.joiners import DocumentJoiner

from haystack.components.routers import FileTypeRouter
from pathlib import Path
from knowledge_graph_component import KnowledgeGraphGenerator
from langchaindocument_component import DocumentToLangChainConverter
from synthetic_test_components import SyntheticTestGenerator,\
                                                TestDatasetSaver
                                        
                            

# Load environment variables
load_dotenv(".env")

@super_component
class SDGGenerator:
    
    def __init__(self, 
                 provided_query_distribution, 
                 provided_test_size, 
                 provided_llm_model, 
                 provided_embedder_model,
                 sd_file_name,
                 openai_api_key=None):

        

        # Core routing and joining components  
        file_router = FileTypeRouter(mime_types=["text/plain", "application/pdf", "text/html"])
        doc_joiner = DocumentJoiner()  # Joins documents from different branches

        # Input converters for each file type
        pdf_converter = PyPDFToDocument()
        html_converter = HTMLToDocument()  
        link_fetcher = LinkContentFetcher()

        preprocessor = DocumentPreprocessor(split_by='sentence',
                                                    split_length=50,
                                                    split_overlap=5,
                                                    remove_empty_lines = True,
                                                    remove_extra_whitespaces = True,
                                                    )
        langchain_doc_converter = DocumentToLangChainConverter()
        
        # Initialize KnowledgeGraphGenerator with explicit model parameters
        kg_generator = KnowledgeGraphGenerator(
            llm_model=provided_llm_model,
            embedder_model=provided_embedder_model,
            apply_transforms=True,
            openai_api_key=openai_api_key
        )
        
        # Initialize SyntheticTestGenerator with explicit model parameters
        test_generator = SyntheticTestGenerator(
            test_size=provided_test_size,  # Larger test set for multiple sources
            llm_model=provided_llm_model,
            embedder_model=provided_embedder_model,
            query_distribution=provided_query_distribution,
            openai_api_key=openai_api_key
        )
        test_saver = TestDatasetSaver(default_output_path=sd_file_name)
        
        # Initialize pipeline
        self.pipeline = Pipeline()

        # Add all components to the pipeline with unique names
        self.pipeline.add_component("link_fetcher", link_fetcher)
        self.pipeline.add_component("html_converter", html_converter)
        self.pipeline.add_component("file_type_router", file_router)
        self.pipeline.add_component("pdf_converter", pdf_converter)
        self.pipeline.add_component("doc_joiner", doc_joiner)
        self.pipeline.add_component("doc_preprocessor", preprocessor)
        self.pipeline.add_component("lg_doc_converter", langchain_doc_converter)
        self.pipeline.add_component("kg_generator", kg_generator)
        self.pipeline.add_component("test_generator", test_generator)
        self.pipeline.add_component("test_saver", test_saver)

        # Web data branch
        self.pipeline.connect("link_fetcher.streams", "html_converter.sources")
        self.pipeline.connect("html_converter.documents", "doc_joiner.documents")

        # PDF file branch
        self.pipeline.connect("file_type_router.application/pdf", "pdf_converter.sources")
        self.pipeline.connect("pdf_converter.documents", "doc_joiner.documents")

        # Main processing path
        self.pipeline.connect("doc_joiner", "doc_preprocessor")
        self.pipeline.connect('doc_preprocessor', 'lg_doc_converter')
        self.pipeline.connect("lg_doc_converter.langchain_documents", "kg_generator.documents")
        self.pipeline.connect("kg_generator.knowledge_graph", "test_generator.knowledge_graph")
        self.pipeline.connect("lg_doc_converter.langchain_documents", "test_generator.documents")
        self.pipeline.connect("test_generator.testset", "test_saver.testset")
        
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


    query_dist = [
                    ("single_hop", 0.3),
                    ("multi_hop_specific", 0.3), 
                    ("multi_hop_abstract", 0.4)
                ]
    llm_model = "gpt-4o-mini"
    embedder_model = "text-embedding-3-small"
    file_name ="data_for_eval/synthetic_tests_advanced_branching_2.csv"
    
    # Create SDGGenerator with explicit model parameters
    sdg_generator = SDGGenerator(
        provided_query_distribution=query_dist,
        provided_test_size=2,
        provided_llm_model=llm_model,
        provided_embedder_model=embedder_model,
        sd_file_name=file_name,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )

    # Run pipeline with both input types
    result = sdg_generator.run(urls=urls, sources=files)