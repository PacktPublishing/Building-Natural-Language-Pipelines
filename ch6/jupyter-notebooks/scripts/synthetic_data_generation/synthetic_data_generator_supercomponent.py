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
from haystack.components.embedders import OpenAITextEmbedder
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret

                                        
                            

# Load environment variables
load_dotenv(".env")

# Helper function to create fresh generator and embedder instances
def create_llm_components():
    """Create fresh instances of generator and embedder.
    
    Each component in the pipeline requires its own generator and embedder instances
    to avoid conflicts during parallel execution. This function creates new instances
    with the same configuration.
    
    Returns:
        tuple: (generator, embedder) - Fresh instances of OpenAI generator and embedder
    """
    # You can use OpenAI models:
    generator = OpenAIGenerator(
        model="gpt-4o-mini",
        api_key=Secret.from_token(os.getenv("OPENAI_API_KEY"))
    )
    embedder = OpenAITextEmbedder(
        model="text-embedding-3-small",
        api_key=Secret.from_token(os.getenv("OPENAI_API_KEY"))
    )
    
    # Or use Ollama models (uncomment to use):
    # from haystack_integrations.components.generators.ollama import OllamaGenerator
    # from haystack_integrations.components.embedders.ollama import OllamaTextEmbedder
    # 
    # generator = OllamaGenerator(
    #     model="mistral-nemo:12b",
    #     generation_kwargs={
    #         "num_predict": 100,
    #         "temperature": 0.9,
    #     }
    # )
    # embedder = OllamaTextEmbedder(model="nomic-embed-text")
    
    return generator, embedder


@super_component
class SDGGenerator:
    """Synthetic Data Generator SuperComponent for creating test datasets from documents.
    
    This component orchestrates a pipeline that:
    1. Fetches and converts documents (PDFs, HTML, web content)
    2. Generates knowledge graphs from the documents
    3. Creates synthetic test datasets with questions, answers, and ground truth
    
    Each sub-component (KnowledgeGraphGenerator, SyntheticTestGenerator) receives
    its own generator and embedder instances to prevent conflicts during execution.
    """
    
    def __init__(self, 
                 provided_query_distribution, 
                 provided_test_size, 
                 sd_file_name):
        """
        Initialize the Synthetic Data Generator SuperComponent.
        
        Args:
            provided_query_distribution (list[tuple]): Distribution of query types for synthetic test generation.
                Format: [(query_type, probability), ...]
                Example: [("single_hop", 0.3), ("multi_hop_specific", 0.3), ("multi_hop_abstract", 0.4)]
            provided_test_size (int): Number of synthetic tests to generate
            sd_file_name (str): Output file path for synthetic dataset (CSV format)
        
        Note:
            API keys for LLM providers (OpenAI, Ollama, etc.) should be configured through
            environment variables or passed directly to the create_llm_components() function.
        """
        self.query_distribution = provided_query_distribution
        self.test_size = provided_test_size
        self.sd_file_name = sd_file_name
        
        self._build_pipeline()
    
    def _build_pipeline(self):
        """Build the synthetic data generation pipeline with initialized components.
        
        Creates separate generator and embedder instances for each component that requires them
        (KnowledgeGraphGenerator and SyntheticTestGenerator). This prevents conflicts that can
        occur when multiple components share the same generator/embedder instances during execution.
        
        Pipeline structure:
        - Document Processing: Fetch, convert, join, and preprocess documents
        - Knowledge Graph: Generate structured knowledge representation
        - Test Generation: Create synthetic test datasets
        - Saving: Persist the test dataset to disk
        """
        
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
        # Note: Each component receives its own generator and embedder instances to avoid
        # conflicts during pipeline execution. Sharing instances can cause state issues.
        
        # Create dedicated instances for knowledge graph generation
        kg_gen, kg_embed = create_llm_components()
        kg_generator = KnowledgeGraphGenerator(
            generator=kg_gen,
            embedder=kg_embed,
            apply_transforms=True
        )

        # Create separate instances for synthetic test generation
        test_gen, test_embed = create_llm_components()
        test_generator = SyntheticTestGenerator(
            generator=test_gen,
            embedder=test_embed,
            test_size=self.test_size,
            query_distribution=self.query_distribution,
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
    """
    Example usage of SDGGenerator SuperComponent.
    
    This example demonstrates how to:
    1. Configure query distribution for different test types
    2. Combine multiple data sources (URLs and PDF files)
    3. Generate a synthetic test dataset
    
    The generator creates separate LLM instances for each component internally,
    ensuring stable execution without conflicts between components.
    """

    # Define sources: separate URLs and files
    pdf_file = Path("./data_for_indexing/howpeopleuseai.pdf")
    
    # URLs for web content (will be fetched and converted to documents)
    urls = [
            "https://www.bbc.com/news/articles/c2l799gxjjpo",
            "https://www.brookings.edu/articles/how-artificial-intelligence-is-transforming-the-world/"
    ]
    # Files for local content (PDFs will be converted to documents)
    files = [pdf_file]

    # Define query distribution:
    # - 30% single-hop questions (simple, direct questions)
    # - 30% multi-hop specific questions (require connecting multiple pieces of information)
    # - 40% multi-hop abstract questions (require reasoning across multiple concepts)
    query_dist = [
                    ("single_hop", 0.3),
                    ("multi_hop_specific", 0.3), 
                    ("multi_hop_abstract", 0.4)
                ]
    file_name = "data_for_eval/synthetic_tests_advanced_branching_10.csv"
    
    # Create SDGGenerator with refactored architecture
    # Each internal component (KG generator, test generator) receives its own LLM instances
    sdg_generator = SDGGenerator(
        provided_query_distribution=query_dist,
        provided_test_size=10,
        sd_file_name=file_name
    )

    # Run pipeline with both input types
    # The pipeline will:
    # 1. Fetch and convert all documents
    # 2. Generate a knowledge graph
    # 3. Create synthetic test cases
    # 4. Save results to the specified CSV file
    result = sdg_generator.run(urls=urls, sources=files)
    
    print(f"\n✅ Synthetic dataset generated successfully!")
    print(f"📁 Saved to: {result.get('saved_path', file_name)}")