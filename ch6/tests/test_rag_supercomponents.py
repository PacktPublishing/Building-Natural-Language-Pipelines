#!/usr/bin/env python3
"""
Tests for RAG SuperComponents (indexing.py, naiverag.py, hybridrag.py)

These tests validate the functionality of custom Haystack SuperComponents for RAG pipelines.
"""

import pytest
import pandas as pd
import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the scripts directory to the Python path for imports
current_dir = Path(__file__).parent  # ch6/tests/
project_root = current_dir.parent    # ch6/
scripts_dir = project_root / "jupyter-notebooks" / "scripts"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir / "rag"))

from haystack.dataclasses import Document as HaystackDocument
from haystack import Pipeline

# Mock the Elasticsearch document store to avoid requiring actual Elasticsearch
@pytest.fixture
def mock_document_store():
    """Create a mock document store for testing."""
    mock_store = Mock()
    mock_store.count_documents.return_value = 0
    return mock_store


class TestIndexingPipelineSuperComponent:
    """Test cases for the IndexingPipelineSuperComponent."""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_component_initialization(self, mock_document_store):
        """Test 1: Component initializes correctly with default and custom parameters."""
        from indexing import IndexingPipelineSuperComponent
        
        # Test default initialization
        indexing_sc = IndexingPipelineSuperComponent(
            document_store=mock_document_store
        )
        assert indexing_sc.embedder_model == "text-embedding-3-small"
        assert indexing_sc.openai_api_key == "test-key"
        assert hasattr(indexing_sc, 'pipeline')
        assert isinstance(indexing_sc.pipeline, Pipeline)
        
        # Test custom initialization  
        indexing_sc_custom = IndexingPipelineSuperComponent(
            document_store=mock_document_store,
            embedder_model="text-embedding-3-large",
            openai_api_key="custom-key"
        )
        assert indexing_sc_custom.embedder_model == "text-embedding-3-large"
        assert indexing_sc_custom.openai_api_key == "custom-key"
    
    def test_missing_api_key_raises_error(self, mock_document_store):
        """Test 2: Component raises error when OpenAI API key is missing."""
        from indexing import IndexingPipelineSuperComponent
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                IndexingPipelineSuperComponent(document_store=mock_document_store)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_pipeline_components_added(self, mock_document_store):
        """Test 3: Pipeline contains all expected components."""
        from indexing import IndexingPipelineSuperComponent
        
        indexing_sc = IndexingPipelineSuperComponent(
            document_store=mock_document_store
        )
        
        # Check that all expected components are in the pipeline
        expected_components = [
            "link_fetcher", "html_converter", "file_type_router", 
            "pdf_converter", "doc_joiner", "doc_preprocessor", 
            "doc_embedder", "writer"
        ]
        
        for component_name in expected_components:
            assert component_name in indexing_sc.pipeline.graph.nodes()
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_input_output_mappings(self, mock_document_store):
        """Test 4: Input and output mappings are correctly configured."""
        from indexing import IndexingPipelineSuperComponent
        
        indexing_sc = IndexingPipelineSuperComponent(
            document_store=mock_document_store
        )
        
        # Check input mappings
        assert "urls" in indexing_sc.input_mapping
        assert "sources" in indexing_sc.input_mapping
        assert "link_fetcher.urls" in indexing_sc.input_mapping["urls"]
        assert "file_type_router.sources" in indexing_sc.input_mapping["sources"]


class TestNaiveRAGSuperComponent:
    """Test cases for the NaiveRAGSuperComponent."""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_component_initialization(self, mock_document_store):
        """Test 1: Component initializes correctly with default and custom parameters."""
        from naiverag import NaiveRAGSuperComponent
        
        # Test default initialization
        naive_rag_sc = NaiveRAGSuperComponent(
            document_store=mock_document_store
        )
        assert naive_rag_sc.embedder_model == "text-embedding-3-small"
        assert naive_rag_sc.llm_model == "gpt-4o-mini"
        assert naive_rag_sc.top_k == 3
        assert naive_rag_sc.openai_api_key == "test-key"
        assert hasattr(naive_rag_sc, 'pipeline')
        assert isinstance(naive_rag_sc.pipeline, Pipeline)
        
        # Test custom initialization
        naive_rag_sc_custom = NaiveRAGSuperComponent(
            document_store=mock_document_store,
            embedder_model="text-embedding-3-large",
            llm_model="gpt-4", 
            top_k=5,
            openai_api_key="custom-key"
        )
        assert naive_rag_sc_custom.embedder_model == "text-embedding-3-large"
        assert naive_rag_sc_custom.llm_model == "gpt-4"
        assert naive_rag_sc_custom.top_k == 5
        assert naive_rag_sc_custom.openai_api_key == "custom-key"
    
    def test_missing_api_key_raises_error(self, mock_document_store):
        """Test 2: Component raises error when OpenAI API key is missing."""
        from naiverag import NaiveRAGSuperComponent
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                NaiveRAGSuperComponent(document_store=mock_document_store)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_pipeline_components_added(self, mock_document_store):
        """Test 3: Pipeline contains all expected components."""
        from naiverag import NaiveRAGSuperComponent
        
        naive_rag_sc = NaiveRAGSuperComponent(
            document_store=mock_document_store
        )
        
        # Check that all expected components are in the pipeline
        expected_components = [
            "text_embedder", "retriever", "prompt_builder", "llm"
        ]
        
        for component_name in expected_components:
            assert component_name in naive_rag_sc.pipeline.graph.nodes()
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_input_output_mappings(self, mock_document_store):
        """Test 4: Input and output mappings are correctly configured."""
        from naiverag import NaiveRAGSuperComponent
        
        naive_rag_sc = NaiveRAGSuperComponent(
            document_store=mock_document_store
        )
        
        # Check input mappings - query should map to multiple components
        assert "query" in naive_rag_sc.input_mapping
        query_mappings = naive_rag_sc.input_mapping["query"]
        assert "text_embedder.text" in query_mappings
        assert "prompt_builder.question" in query_mappings
        
        # Check output mappings
        assert "replies" in naive_rag_sc.output_mapping.values()
        assert "documents" in naive_rag_sc.output_mapping.values()


class TestHybridRAGSuperComponent:
    """Test cases for the HybridRAGSuperComponent."""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_component_initialization(self, mock_document_store):
        """Test 1: Component initializes correctly with default and custom parameters."""
        from hybridrag import HybridRAGSuperComponent
        
        # Test default initialization
        hybrid_rag_sc = HybridRAGSuperComponent(
            document_store=mock_document_store
        )
        assert hybrid_rag_sc.embedder_model == "text-embedding-3-small"
        assert hybrid_rag_sc.llm_model == "gpt-4o-mini"
        assert hybrid_rag_sc.top_k == 3
        assert hybrid_rag_sc.ranker_model == "BAAI/bge-reranker-base"
        assert hybrid_rag_sc.openai_api_key == "test-key"
        assert hasattr(hybrid_rag_sc, 'pipeline')
        assert isinstance(hybrid_rag_sc.pipeline, Pipeline)
        
        # Test custom initialization
        hybrid_rag_sc_custom = HybridRAGSuperComponent(
            document_store=mock_document_store,
            embedder_model="text-embedding-3-large",
            llm_model="gpt-4",
            top_k=5, 
            ranker_model="custom-ranker",
            openai_api_key="custom-key"
        )
        assert hybrid_rag_sc_custom.embedder_model == "text-embedding-3-large"
        assert hybrid_rag_sc_custom.llm_model == "gpt-4"
        assert hybrid_rag_sc_custom.top_k == 5
        assert hybrid_rag_sc_custom.ranker_model == "custom-ranker"
        assert hybrid_rag_sc_custom.openai_api_key == "custom-key"
    
    def test_missing_api_key_raises_error(self, mock_document_store):
        """Test 2: Component raises error when OpenAI API key is missing."""
        from hybridrag import HybridRAGSuperComponent
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                HybridRAGSuperComponent(document_store=mock_document_store)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_pipeline_components_added(self, mock_document_store):
        """Test 3: Pipeline contains all expected components for hybrid retrieval."""
        from hybridrag import HybridRAGSuperComponent
        
        hybrid_rag_sc = HybridRAGSuperComponent(
            document_store=mock_document_store
        )
        
        # Check that all expected components are in the pipeline
        expected_components = [
            "text_embedder", "embedding_retriever", "bm25_retriever",
            "document_joiner", "ranker", "prompt_builder", "llm"
        ]
        
        for component_name in expected_components:
            assert component_name in hybrid_rag_sc.pipeline.graph.nodes()
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_dual_retrieval_connections(self, mock_document_store):
        """Test 4: Pipeline correctly connects dual retrieval paths."""
        from hybridrag import HybridRAGSuperComponent
        
        hybrid_rag_sc = HybridRAGSuperComponent(
            document_store=mock_document_store
        )
        
        # Check that both retrievers connect to document joiner
        pipeline_connections = hybrid_rag_sc.pipeline.graph.edges()
        
        # Find connections from retrievers to joiner
        embedding_to_joiner = False
        bm25_to_joiner = False
        
        for connection in pipeline_connections:
            if connection[0] == "embedding_retriever" and connection[1] == "document_joiner":
                embedding_to_joiner = True
            elif connection[0] == "bm25_retriever" and connection[1] == "document_joiner":
                bm25_to_joiner = True
        
        assert embedding_to_joiner, "Embedding retriever should connect to document joiner"
        assert bm25_to_joiner, "BM25 retriever should connect to document joiner"
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_input_output_mappings(self, mock_document_store):
        """Test 5: Input and output mappings are correctly configured for hybrid retrieval."""
        from hybridrag import HybridRAGSuperComponent
        
        hybrid_rag_sc = HybridRAGSuperComponent(
            document_store=mock_document_store
        )
        
        # Check input mappings - query should map to both retrievers and other components
        assert "query" in hybrid_rag_sc.input_mapping
        query_mappings = hybrid_rag_sc.input_mapping["query"]
        assert "text_embedder.text" in query_mappings
        assert "bm25_retriever.query" in query_mappings
        assert "ranker.query" in query_mappings
        assert "prompt_builder.question" in query_mappings
        
        # Check output mappings
        assert "replies" in hybrid_rag_sc.output_mapping.values()
        assert "documents" in hybrid_rag_sc.output_mapping.values()


def run_tests():
    """Run all tests in this module."""
    print("🧪 Running RAG SuperComponent Tests")
    print("=" * 50)
    
    # Create a mock document store
    mock_ds = Mock()
    mock_ds.count_documents.return_value = 0
    
    # Test IndexingPipelineSuperComponent
    print("\n📁 Testing IndexingPipelineSuperComponent...")
    indexing_tests = TestIndexingPipelineSuperComponent()
    try:
        indexing_tests.test_component_initialization(mock_ds)
        indexing_tests.test_missing_api_key_raises_error(mock_ds)
        indexing_tests.test_pipeline_components_added(mock_ds)
        indexing_tests.test_input_output_mappings(mock_ds)
        print("✅ IndexingPipelineSuperComponent tests passed")
    except Exception as e:
        print(f"❌ IndexingPipelineSuperComponent tests failed: {e}")
    
    # Test NaiveRAGSuperComponent
    print("\n🔍 Testing NaiveRAGSuperComponent...")
    naive_tests = TestNaiveRAGSuperComponent()
    try:
        naive_tests.test_component_initialization(mock_ds)
        naive_tests.test_missing_api_key_raises_error(mock_ds)
        naive_tests.test_pipeline_components_added(mock_ds)
        naive_tests.test_input_output_mappings(mock_ds)
        print("✅ NaiveRAGSuperComponent tests passed")
    except Exception as e:
        print(f"❌ NaiveRAGSuperComponent tests failed: {e}")
    
    # Test HybridRAGSuperComponent
    print("\n🔀 Testing HybridRAGSuperComponent...")
    hybrid_tests = TestHybridRAGSuperComponent()
    try:
        hybrid_tests.test_component_initialization(mock_ds)
        hybrid_tests.test_missing_api_key_raises_error(mock_ds)
        hybrid_tests.test_pipeline_components_added(mock_ds)
        hybrid_tests.test_dual_retrieval_connections(mock_ds)
        hybrid_tests.test_input_output_mappings(mock_ds)
        print("✅ HybridRAGSuperComponent tests passed")
    except Exception as e:
        print(f"❌ HybridRAGSuperComponent tests failed: {e}")
    
    print("\n🎉 RAG SuperComponent testing completed!")


if __name__ == "__main__":
    run_tests()