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
        """
        Initialize the Synthetic Data Generator SuperComponent.
        
        Args:
            provided_query_distribution: Distribution of query types for synthetic test generation
            provided_test_size: Number of synthetic tests to generate
            provided_llm_model (str): LLM model name for generation tasks
            provided_embedder_model (str): Embedding model name for vector operations
            sd_file_name (str): Output file name for synthetic dataset
            openai_api_key (Optional[str]): OpenAI API key. If None, will use environment variable.
        """
        self.query_distribution = provided_query_distribution
        self.test_size = provided_test_size
        self.llm_model = provided_llm_model
        self.embedder_model = provided_embedder_model
        self.sd_file_name = sd_file_name
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")
        
        self._build_pipeline()
    
    def _build_pipeline(self):
        """Build the synthetic data generation pipeline with initialized components."""
        
        # --- 1. Initialize Document Processing Components ---
        
        # Core routing and joining components  
        file_router = FileTypeRouter(mime_types=["text/plain", "application/pdf", "text/html"])
        doc_joiner = DocumentJoiner()  # Joins documents from different branches

        # Input converters for each file type
        pdf_converter = PyPDFToDocument()
        html_converter = HTMLToDocument()  
        link_fetcher = LinkContentFetcher()

        # Document preprocessor for splitting and cleaning
        preprocessor = DocumentPreprocessor(
            split_by='sentence',
            split_length=50,
            split_overlap=5,
            remove_empty_lines=True,
            remove_extra_whitespaces=True,
        )
        
        # Convert Haystack documents to LangChain format
        langchain_doc_converter = DocumentToLangChainConverter()
        
        # --- 2. Initialize Knowledge Graph and Test Generation Components ---
        
        # Knowledge Graph Generator with explicit model parameters
        kg_generator = KnowledgeGraphGenerator(
            llm_model=self.llm_model,
            embedder_model=self.embedder_model,
            apply_transforms=True,
            openai_api_key=self.openai_api_key
        )
        
        # Synthetic Test Generator with explicit model parameters
        test_generator = SyntheticTestGenerator(
            test_size=self.test_size,
            llm_model=self.llm_model,
            embedder_model=self.embedder_model,
            query_distribution=self.query_distribution,
            openai_api_key=self.openai_api_key
        )
        
        # Test Dataset Saver
        test_saver = TestDatasetSaver(default_output_path=self.sd_file_name)
        
        # --- 3. Build the Pipeline ---
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

        # --- 4. Connect the Components in a Graph ---
        
        # Web data branch: URLs -> HTML conversion -> document joiner
        self.pipeline.connect("link_fetcher.streams", "html_converter.sources")
        self.pipeline.connect("html_converter.documents", "doc_joiner.documents")

        # PDF file branch: Files -> PDF conversion -> document joiner
        self.pipeline.connect("file_type_router.application/pdf", "pdf_converter.sources")
        self.pipeline.connect("pdf_converter.documents", "doc_joiner.documents")

        # Main processing path: Documents -> Preprocessing -> LangChain conversion -> Knowledge Graph -> Test Generation -> Saving
        self.pipeline.connect("doc_joiner", "doc_preprocessor")
        self.pipeline.connect('doc_preprocessor', 'lg_doc_converter')
        self.pipeline.connect("lg_doc_converter.langchain_documents", "kg_generator.documents")
        self.pipeline.connect("kg_generator.knowledge_graph", "test_generator.knowledge_graph")
        self.pipeline.connect("lg_doc_converter.langchain_documents", "test_generator.documents")
        self.pipeline.connect("test_generator.testset", "test_saver.testset")
        
        # --- 5. Define Input and Output Mappings ---
        self.input_mapping = {
            "urls": ["link_fetcher.urls"],
            "sources": ["file_type_router.sources"]
        }

        self.output_mapping = {
            "test_saver.saved_path": "saved_path"
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
    file_name ="data_for_eval/synthetic_tests_advanced_branching_10.csv"
    
    # Create SDGGenerator with explicit model parameters
    sdg_generator = SDGGenerator(
        provided_query_distribution=query_dist,
        provided_test_size=10,
        provided_llm_model=llm_model,
        provided_embedder_model=embedder_model,
        sd_file_name=file_name,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )

    # Run pipeline with both input types
    result = sdg_generator.run(urls=urls, sources=files)