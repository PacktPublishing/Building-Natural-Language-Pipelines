#!/usr/bin/env python3
"""
Haystack 2.0 components for synthetic test data generation using Ragas.

This module provides components that can be integrated into Haystack pipelines for:
1. Generating synthetic test datasets from knowledge graphs
2. Generating synthetic test datasets from documents directly
3. Saving test datasets to various formats (CSV, JSON, etc.)
"""

from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import os
from pathlib import Path

from haystack import component, logging
from haystack.dataclasses import Document as HaystackDocument
from langchain_core.documents import Document as LangChainDocument

from ragas.testset.graph import KnowledgeGraph
from ragas.testset import TestsetGenerator
from ragas.testset.synthesizers import (
    SingleHopSpecificQuerySynthesizer,
    MultiHopAbstractQuerySynthesizer,
    MultiHopSpecificQuerySynthesizer
)

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
  


logger = logging.getLogger(__name__)


@component
class SyntheticTestGenerator:
    """
    Haystack 2.0 component for generating synthetic test datasets using Ragas.
    
    This component can generate synthetic question-answer pairs from either:
    1. A knowledge graph (recommended for better quality)
    2. Documents directly (fallback option)
    
    Usage:
        ```python
        generator = SyntheticTestGenerator(
            testset_size=20,
            llm_model="gpt-4o-mini"
        )
        
        # Use with knowledge graph (preferred)
        result = generator.run(knowledge_graph=kg, documents=docs)
        
        # Or use with documents only
        result = generator.run(documents=docs)
        ```
    """
    
    def __init__(
        self,
        testset_size: int = 10,
        llm_model: str = "gpt-4o-mini",
        query_distribution: Optional[List[Tuple[str, float]]] = None,
        openai_api_key: Optional[str] = None,
        max_testset_size: Optional[int] = None
    ):
        """
        Initialize the SyntheticTestGenerator component.
        
        Args:
            testset_size (int): Number of synthetic test cases to generate.
            llm_model (str): OpenAI model for test generation.
            query_distribution (Optional[List[Tuple[str, float]]]): Distribution of query types.
                Format: [("single_hop", 0.5), ("multi_hop_abstract", 0.25), ("multi_hop_specific", 0.25)]
            openai_api_key (Optional[str]): OpenAI API key override.
            max_testset_size (Optional[int]): Maximum testset size to prevent API timeouts. If None, uses testset_size.
        """
        self.testset_size = testset_size
        self.llm_model = llm_model
        self.openai_api_key = openai_api_key
        self.max_testset_size = max_testset_size
        
        # Set default query distribution if not provided
        self.query_distribution = query_distribution or [
            ("single_hop", 0.5),
            ("multi_hop_abstract", 0.25),
            ("multi_hop_specific", 0.25)
        ]
        
        self._initialize_models()
    
    def _validate_environment(self):
        """Validate that the environment is properly set up for test generation."""
        # Check API key
        api_key = self.openai_api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables or parameters.")
        
        logger.info("Environment validation successful")
    
    def _initialize_models(self):
        """Initialize LLM and embedding models."""
        try:
            # Check for API key
            api_key = self.openai_api_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")
            
            # Initialize using LangchainLLMWrapper for compatibility
            chat_openai_kwargs = {"model": self.llm_model}
            if api_key:
                chat_openai_kwargs["openai_api_key"] = api_key
                
            self.llm = LangchainLLMWrapper(ChatOpenAI(**chat_openai_kwargs))
            
            embeddings_kwargs = {}
            if api_key:
                embeddings_kwargs["openai_api_key"] = api_key
                
            self.embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(**embeddings_kwargs))
            logger.info(f"Using LangchainLLMWrapper with model: {self.llm_model}")
                
            logger.info(f"Initialized SyntheticTestGenerator with model: {self.llm_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            raise
    
    def _create_query_synthesizers(self) -> List[Tuple[Any, float]]:
        """Create query synthesizers based on the configured distribution."""
        synthesizers = []
        
        for query_type, weight in self.query_distribution:
            if query_type == "single_hop":
                synthesizer = SingleHopSpecificQuerySynthesizer(llm=self.llm)
            elif query_type == "multi_hop_abstract":
                synthesizer = MultiHopAbstractQuerySynthesizer(llm=self.llm)
            elif query_type == "multi_hop_specific":
                synthesizer = MultiHopSpecificQuerySynthesizer(llm=self.llm)
            else:
                logger.warning(f"Unknown query type: {query_type}, skipping")
                continue
            
            synthesizers.append((synthesizer, weight))
        
        return synthesizers
    
    @component.output_types(
        testset=pd.DataFrame, 
        testset_size=int, 
        generation_method=str, 
        success=bool
    )
    def run(
        self, 
        documents: List[LangChainDocument],
        knowledge_graph: Optional[KnowledgeGraph] = None
    ) -> Dict[str, Any]:
        """
        Generate synthetic test dataset.
        
        Args:
            documents (List[LangChainDocument]): Source documents for test generation.
            knowledge_graph (Optional[KnowledgeGraph]): Pre-built knowledge graph (preferred).
            
        Returns:
            Dict containing:
                - testset (pd.DataFrame): Generated test dataset
                - testset_size (int): Actual number of tests generated
                - generation_method (str): Method used ("knowledge_graph" or "documents")
                - success (bool): Whether generation was successful
        """
        if not documents:
            logger.error("No documents provided for test generation")
            return {
                "testset": pd.DataFrame(),
                "testset_size": 0,
                "generation_method": "none",
            }
        
        # Validate environment before proceeding
        try:
            self._validate_environment()
        except (ValueError, ConnectionError) as e:
            logger.error(f"Environment validation failed: {e}")
            return {
                "testset": pd.DataFrame(),
                "testset_size": 0,
                "generation_method": "env_validation_failed",
            }
        
        try:
            # Prefer knowledge graph method if available
            if knowledge_graph is not None:
                logger.info(f"Generating {self.testset_size} test cases using knowledge graph")
                try:
                    testset = self._generate_from_knowledge_graph(knowledge_graph)
                    method = "knowledge_graph"
                except Exception as kg_error:
                    logger.warning(f"Knowledge graph generation failed: {kg_error}. Falling back to document-based generation.")
                    testset = self._generate_from_documents(documents)
                    method = "documents_fallback"
            else:
                logger.info(f"Generating {self.testset_size} test cases using documents directly")
                testset = self._generate_from_documents(documents)
                method = "documents"
            
            # Convert to pandas DataFrame
            df = testset.to_pandas()
            actual_size = len(df)
            
            logger.info(f"Successfully generated {actual_size} synthetic test cases using {method}")
            
            return {
                "testset": df,
                "testset_size": actual_size,
                "generation_method": method,
            }
            
        except ConnectionError as e:
            logger.error(f"Connection error during test generation: {e}")
            return {
                "testset": pd.DataFrame(),
                "testset_size": 0,
                "generation_method": "failed_connection",
            }
        except Exception as e:
            logger.error(f"Failed to generate synthetic tests: {e}")
            return {
                "testset": pd.DataFrame(),
                "testset_size": 0,
                "generation_method": "failed",
            }
    
    def _generate_from_knowledge_graph(self, knowledge_graph: KnowledgeGraph):
        """Generate tests using a knowledge graph."""
        try:
            generator = TestsetGenerator(
                llm=self.llm,
                embedding_model=self.embeddings,
                knowledge_graph=knowledge_graph
            )
        except Exception as e:
            logger.error(f"ErrortestGenerator: {type(e).__name__}: {e}")
            raise Exception(f"Test generstor failed: {e}")
        try:   
            query_distribution = self._create_query_synthesizers()
        except Exception as e:
            logger.error(f"Error query distribution: {type(e).__name__}: {e}")
            raise Exception(f"Query distribution failes: {e}")
        
        try:
            # Use max_testset_size if specified, otherwise use full testset_size
            actual_size = min(self.testset_size, self.max_testset_size) if self.max_testset_size else self.testset_size
            
            logger.info(f"Attempting to generate {actual_size} test cases from knowledge graph")
            
            result = generator.generate(
                testset_size=actual_size,
                query_distribution=query_distribution
            )
            return result
            
        except Exception as e:
            logger.error(f"Error generator: {type(e).__name__}: {e}")
            raise Exception(f"generator: {e}")
    
    def _generate_from_documents(self, documents: List[LangChainDocument]):
        """Generate tests directly from documents."""
        try:
            # Filter documents to ensure they have sufficient content (>100 tokens)
            # Rough estimate: 1 token ≈ 4 characters for English text
            min_content_length = 400  # ~100 tokens
            filtered_docs = [
                doc for doc in documents 
                if len(doc.page_content) >= min_content_length
            ]
            
            if not filtered_docs:
                logger.warning("No documents meet minimum length requirement (100+ tokens). Using original documents.")
                filtered_docs = documents
                # If still too short, concatenate documents
                if len(documents) > 1:
                    combined_content = " ".join([doc.page_content for doc in documents])
                    if len(combined_content) >= min_content_length:
                        from langchain_core.documents import Document as LangChainDocument
                        filtered_docs = [LangChainDocument(page_content=combined_content, metadata={})]
            
            generator = TestsetGenerator(
                llm=self.llm,
                embedding_model=self.embeddings
            )
            
            # Use max_testset_size if specified, otherwise use full testset_size
            actual_size = min(self.testset_size, self.max_testset_size) if self.max_testset_size else self.testset_size
            
            # Create query distribution for generate_with_langchain_docs
            # In recent versions of Ragas, the query_distribution for
            # ``generate_with_langchain_docs`` is expected to be a list of
            # ``(synthesizer, probability)`` tuples (similar to the
            # knowledge‐graph generation method). Passing a plain dictionary
            # will cause unpacking errors when Ragas iterates over the
            # distribution. To remain compatible with both newer and older
            # versions, reuse the synthesizer objects created in
            # ``_create_query_synthesizers``.
            query_dist = self._create_query_synthesizers()

            return generator.generate_with_langchain_docs(
                documents=filtered_docs,
                testset_size=actual_size,
                query_distribution=query_dist,
                raise_exceptions=True,
                with_debugging_logs=True
            )
        except Exception as e:
            logger.error(f"Document-based generation failed: {e}")
            # Check if it's a length-related error and provide helpful guidance
            if "too short" in str(e).lower():
                logger.error("Documents are too short for Ragas test generation. Consider:")
                logger.error("1. Using longer documents (>100 tokens)")
                logger.error("2. Combining multiple documents")
                logger.error("3. Using the knowledge graph approach instead")
            # Create a minimal fallback dataset
            return self._create_fallback_testset(documents)
    
    def _create_fallback_testset(self, documents: List[LangChainDocument]):
        """Create a minimal fallback testset when generation fails."""
        logger.warning("Creating fallback testset due to generation failure")
        
        # Create a simple test dataset structure
        class MockTestset:
            def __init__(self, data):
                self.data = data
            
            def to_pandas(self):
                import pandas as pd
                return pd.DataFrame(self.data)
        
        # Create basic test cases from document content
        test_data = []
        num_tests_to_create = min(self.testset_size, len(documents))
        
        # If we have fewer documents than requested tests, cycle through documents
        for i in range(self.testset_size):
            doc_index = i % len(documents)
            doc = documents[doc_index]
            content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            
            # Create varied questions for the same document if cycling
            question_variants = [
                f"What is discussed in document {doc_index + 1}?",
                f"What are the main topics covered in document {doc_index + 1}?",
                f"Can you summarize the content of document {doc_index + 1}?",
                f"What key information is presented in document {doc_index + 1}?",
                f"What does document {doc_index + 1} explain?"
            ]
            
            question = question_variants[i % len(question_variants)]
            
            test_data.append({
                'question': question,
                'ground_truth': f"Document {doc_index + 1} discusses: {content}",
                'contexts': [content],
                'answer': f"This document covers: {content}"
            })
        
        return MockTestset(test_data)


@component
class TestDatasetSaver:
    """
    Haystack 2.0 component for saving test datasets to various formats.
    
    Supports CSV, JSON, and other pandas-compatible formats.
    """
    
    def __init__(self, default_output_path: Optional[str] = None):
        """
        Initialize the TestDatasetSaver component.
        
        Args:
            default_output_path (Optional[str]): Default path for saving datasets.
        """
        self.default_output_path = default_output_path or "synthetic_testset.csv"
    
    @component.output_types(saved_path=str, success=bool, row_count=int)
    def run(
        self, 
        testset: pd.DataFrame, 
        output_path: Optional[str] = None,
        format: str = "csv"
    ) -> Dict[str, Any]:
        """
        Save the test dataset to a file.
        
        Args:
            testset (pd.DataFrame): Test dataset to save.
            output_path (Optional[str]): Override output path.
            format (str): Output format ("csv", "json", "parquet").
            
        Returns:
            Dict containing save results.
        """
        save_path = output_path or self.default_output_path
        
        try:
            # Ensure we have a valid path
            if not save_path or save_path.strip() == "":
                save_path = "synthetic_testset.csv"
            
            # Ensure output directory exists
            dir_path = os.path.dirname(save_path)
            if dir_path and dir_path != "":
                os.makedirs(dir_path, exist_ok=True)
            
            # Save in requested format
            if format.lower() == "csv":
                testset.to_csv(save_path, index=False)
            elif format.lower() == "json":
                testset.to_json(save_path, orient="records", indent=2)
            elif format.lower() == "parquet":
                testset.to_parquet(save_path, index=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            row_count = len(testset)
            logger.info(f"Successfully saved {row_count} test cases to {save_path}")
            
            return {
                "saved_path": save_path,
                "success": True,
                "row_count": row_count
            }
            
        except Exception as e:
            logger.error(f"Failed to save test dataset to {save_path}: {e}")
            return {
                "saved_path": save_path,
                "success": False,
                "row_count": 0
            }


"""
Sample usage:

if __name__ == "__main__":
    from haystack import Pipeline
    from scripts.synthetic_test_components import SyntheticTestGenerator, TestDatasetSaver
    from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
    from haystack.components.converters import PyPDFToDocument
    from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
    from scripts.knowledge_graph_component import KnowledgeGraphGenerator
    from scripts.synthetic_test_components import DocumentToLangChainConverter
    from pathlib import Path
    import os
    from dotenv import load_dotenv
    load_dotenv()
    # Load documents from PDF files
    pdf_files = [Path("./data_for_indexing/howpeopleuseai.pdf")]
    loader = DirectoryLoader("./data_for_indexing", glob="*.pdf", loader_cls=PyMuPDFLoader)
    docs = loader.load()
    # Create pipeline components
    pdf_converter = PyPDFToDocument()
    doc_cleaner = DocumentCleaner(remove_empty_lines=True, remove_extra_whitespaces=True)
"""