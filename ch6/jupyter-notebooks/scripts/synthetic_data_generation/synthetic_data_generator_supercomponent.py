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
def create_llm_components(embedder_model="text-embedding-3-small"):
    """Create fresh instances of generator and embedder.
    
    Each component in the pipeline requires its own generator and embedder instances
    to avoid conflicts during parallel execution. This function creates new instances
    with the same configuration.
    
    Args:
        embedder_model (str): The embedding model to use. Options:
            - "text-embedding-3-small" (default)
            - "text-embedding-3-large"
    
    Returns:
        tuple: (generator, embedder) - Fresh instances of OpenAI generator and embedder
    """
    # You can use OpenAI models:
    generator = OpenAIGenerator(
        model="gpt-4o-mini",
        api_key=Secret.from_token(os.getenv("OPENAI_API_KEY"))
    )
    embedder = OpenAITextEmbedder(
        model=embedder_model,
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
                 kg_generator_instance,
                 kg_embedder_instance,
                 test_generator_instance,
                 test_embedder_instance,
                 provided_query_distribution, 
                 provided_test_size, 
                 sd_file_name):
        """
        Initialize the Synthetic Data Generator SuperComponent.
        
        Args:
            kg_generator_instance: Generator instance for knowledge graph generation
            kg_embedder_instance: Embedder instance for knowledge graph generation
            test_generator_instance: Generator instance for synthetic test generation
            test_embedder_instance: Embedder instance for synthetic test generation
            provided_query_distribution (list[tuple]): Distribution of query types for synthetic test generation.
                Format: [(query_type, probability), ...]
                Example: [("single_hop", 0.3), ("multi_hop_specific", 0.3), ("multi_hop_abstract", 0.4)]
            provided_test_size (int): Number of synthetic tests to generate
            sd_file_name (str): Output file path for synthetic dataset (CSV format)
        
        Note:
            API keys for LLM providers (OpenAI, Ollama, etc.) should be configured through
            environment variables or passed directly to the create_llm_components() function.
        """
        self.kg_generator_instance = kg_generator_instance
        self.kg_embedder_instance = kg_embedder_instance
        self.test_generator_instance = test_generator_instance
        self.test_embedder_instance = test_embedder_instance
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
        
        # Use the generator and embedder instances provided during initialization
        kg_generator = KnowledgeGraphGenerator(
            generator=self.kg_generator_instance,
            embedder=self.kg_embedder_instance,
            apply_transforms=True
        )

        # Use the separate test generator and embedder instances
        test_generator = SyntheticTestGenerator(
            generator=self.test_generator_instance,
            embedder=self.test_embedder_instance,
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
    3. Generate synthetic test datasets with both small and large embedding models
    
    The generator creates separate LLM instances for each component internally,
    ensuring stable execution without conflicts between components.
    """

    files = [Path("./data_for_indexing/howpeopleuseai.pdf")]
    
    # URLs for web content
    urls = [
            "https://www.bbc.com/news/articles/c2l799gxjjpo",
            "https://www.brookings.edu/articles/how-artificial-intelligence-is-transforming-the-world/"
    ]

    # Define query distribution:
    # - 30% single-hop questions (simple, direct questions)
    # - 30% multi-hop specific questions (require connecting multiple pieces of information)
    # - 40% multi-hop abstract questions (require reasoning across multiple concepts)
    query_dist = [
                    ("single_hop", 0.3),
                    ("multi_hop_specific", 0.3), 
                    ("multi_hop_abstract", 0.4)
                ]
    
    # ========== EXPERIMENT 1: Small Embedding Model ==========
    print("\n" + "="*70)
    print("🔬 EXPERIMENT 1: Generating Synthetic Data with Small Embedding Model")
    print("="*70)
    
    file_name_small = "data_for_eval/synthetic_tests_small_embedding_10.csv"
    
    # Create separate LLM instances for each component with small embedder
    kg_gen_small, kg_embed_small = create_llm_components(embedder_model="text-embedding-3-small")
    test_gen_small, test_embed_small = create_llm_components(embedder_model="text-embedding-3-small")
    
    print(f"📋 Configuration:")
    print(f"   • Embedder: text-embedding-3-small")
    print(f"   • Generator: gpt-4o-mini")
    print(f"   • Test size: 10 samples")
    print(f"   • Output: {file_name_small}")
    
    # Create SDGGenerator for small embeddings
    sdg_generator_small = SDGGenerator(
        kg_generator_instance=kg_gen_small,
        kg_embedder_instance=kg_embed_small,
        test_generator_instance=test_gen_small,
        test_embedder_instance=test_embed_small,
        provided_query_distribution=query_dist,
        provided_test_size=10,
        sd_file_name=file_name_small
    )

    # Run pipeline with both input types
    result_small = sdg_generator_small.run(urls=urls, sources=files)
    
    print(f"\n✅ Small embedding synthetic dataset generated successfully!")
    print(f"📁 Saved to: {result_small.get('saved_path', file_name_small)}")
    
    # ========== EXPERIMENT 2: Large Embedding Model ==========
    print("\n" + "="*70)
    print("🔬 EXPERIMENT 2: Generating Synthetic Data with Large Embedding Model")
    print("="*70)
    
    file_name_large = "data_for_eval/synthetic_tests_large_embedding_10.csv"
    
    # Create separate LLM instances for each component with large embedder
    kg_gen_large, kg_embed_large = create_llm_components(embedder_model="text-embedding-3-large")
    test_gen_large, test_embed_large = create_llm_components(embedder_model="text-embedding-3-large")
    
    print(f"📋 Configuration:")
    print(f"   • Embedder: text-embedding-3-large")
    print(f"   • Generator: gpt-4o-mini")
    print(f"   • Test size: 10 samples")
    print(f"   • Output: {file_name_large}")
    
    # Create SDGGenerator for large embeddings
    sdg_generator_large = SDGGenerator(
        kg_generator_instance=kg_gen_large,
        kg_embedder_instance=kg_embed_large,
        test_generator_instance=test_gen_large,
        test_embedder_instance=test_embed_large,
        provided_query_distribution=query_dist,
        provided_test_size=10,
        sd_file_name=file_name_large
    )

    # Run pipeline with both input types
    result_large = sdg_generator_large.run(urls=urls, sources=files)
    
    print(f"\n✅ Large embedding synthetic dataset generated successfully!")
    print(f"📁 Saved to: {result_large.get('saved_path', file_name_large)}")
    
    # ========== SUMMARY ==========
    print("\n" + "="*70)
    print("🎉 BOTH EXPERIMENTS COMPLETED SUCCESSFULLY!")
    print("="*70)
    print(f"📊 Small Embedding Dataset: {result_small.get('saved_path', file_name_small)}")
    print(f"📊 Large Embedding Dataset: {result_large.get('saved_path', file_name_large)}")
    print("\n✨ You can now use these datasets to evaluate your RAG system!")
    print("="*70)