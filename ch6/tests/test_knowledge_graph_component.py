#!/usr/bin/env python3
"""
Tests for knowledge_graph_component.py

These tests validate the functionality of custom Haystack components for knowledge graph generation.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import List
from pathlib import Path

# Add the scripts directory to the Python path for imports
current_dir = Path(__file__).parent  # ch5/tests/
project_root = current_dir.parent    # ch5/
scripts_dir = project_root / "jupyter-notebooks" / "scripts"
sys.path.insert(0, str(scripts_dir))

from haystack.dataclasses import Document as HaystackDocument
from langchain_core.documents import Document as LangChainDocument
from ragas.testset.graph import KnowledgeGraph, Node, NodeType

from scripts.knowledge_graph_component import (
    KnowledgeGraphGenerator, 
    KnowledgeGraphSaver,
    DocumentToLangChainConverter
)


class TestKnowledgeGraphGenerator:
    """Test cases for the KnowledgeGraphGenerator component."""

    @patch('knowledge_graph_component.LangchainLLMWrapper')
    @patch('knowledge_graph_component.LangchainEmbeddingsWrapper')
    @patch('knowledge_graph_component.ChatOpenAI')
    @patch('knowledge_graph_component.OpenAIEmbeddings')
    def test_component_initialization(self, mock_embeddings, mock_chat, mock_llm_wrapper, mock_emb_wrapper):
        """Test 1: Component initializes correctly with default and custom parameters."""
        # Setup mocks
        mock_chat.return_value = Mock()
        mock_embeddings.return_value = Mock()
        mock_llm_wrapper.return_value = Mock()
        mock_emb_wrapper.return_value = Mock()
        
        # Test default initialization
        generator = KnowledgeGraphGenerator()
        assert generator.llm_model == "gpt-4o-mini"
        assert generator.apply_transforms is True
        assert generator.openai_api_key is None
        
        # Test custom initialization
        generator_custom = KnowledgeGraphGenerator(
            llm_model="gpt-3.5-turbo",
            apply_transforms=False,
            openai_api_key="test-key"
        )
        assert generator_custom.llm_model == "gpt-3.5-turbo"
        assert generator_custom.apply_transforms is False
        assert generator_custom.openai_api_key == "test-key"

    @patch('knowledge_graph_component.LangchainLLMWrapper')
    @patch('knowledge_graph_component.LangchainEmbeddingsWrapper')
    @patch('knowledge_graph_component.ChatOpenAI')
    @patch('knowledge_graph_component.OpenAIEmbeddings')
    def test_empty_document_handling(self, mock_embeddings, mock_chat, mock_llm_wrapper, mock_emb_wrapper):
        """Test 2: Component handles empty document lists gracefully."""
        # Setup mocks
        mock_chat.return_value = Mock()
        mock_embeddings.return_value = Mock()
        mock_llm_wrapper.return_value = Mock()
        mock_emb_wrapper.return_value = Mock()
        
        generator = KnowledgeGraphGenerator(apply_transforms=False)
        
        # Test with empty documents list
        result = generator.run(documents=[])
        
        assert isinstance(result['knowledge_graph'], KnowledgeGraph)
        assert result['node_count'] == 0
        assert result['transform_applied'] is False
        assert len(result['knowledge_graph'].nodes) == 0

    @patch('knowledge_graph_component.default_transforms')
    @patch('knowledge_graph_component.apply_transforms')
    @patch('knowledge_graph_component.LangchainLLMWrapper')
    @patch('knowledge_graph_component.LangchainEmbeddingsWrapper')
    @patch('knowledge_graph_component.ChatOpenAI')
    @patch('knowledge_graph_component.OpenAIEmbeddings')
    def test_successful_graph_creation_with_documents(self, mock_embeddings, mock_chat, 
                                                    mock_llm_wrapper, mock_emb_wrapper,
                                                    mock_apply_transforms, mock_default_transforms):
        """Test 3: Component creates knowledge graph successfully with valid documents."""
        # Setup mocks
        mock_chat.return_value = Mock()
        mock_embeddings.return_value = Mock()
        mock_llm_wrapper.return_value = Mock()
        mock_emb_wrapper.return_value = Mock()
        mock_default_transforms.return_value = []
        mock_apply_transforms.return_value = None
        
        # Create test documents
        test_docs = [
            LangChainDocument(
                page_content="Artificial intelligence is the simulation of human intelligence.",
                metadata={"source": "ai_doc.txt", "topic": "AI"}
            ),
            LangChainDocument(
                page_content="Machine learning is a subset of artificial intelligence.",
                metadata={"source": "ml_doc.txt", "topic": "ML"}
            )
        ]
        
        generator = KnowledgeGraphGenerator(apply_transforms=True)
        result = generator.run(documents=test_docs)
        
        # Verify results
        assert isinstance(result['knowledge_graph'], KnowledgeGraph)
        assert result['node_count'] == 2
        assert result['transform_applied'] is True
        
        # Check that nodes were created correctly
        kg = result['knowledge_graph']
        assert len(kg.nodes) == 2
        
        # Verify first node
        first_node = kg.nodes[0]
        assert first_node.type == NodeType.DOCUMENT
        assert first_node.properties['page_content'] == test_docs[0].page_content
        assert first_node.properties['document_metadata'] == test_docs[0].metadata
        
        # Verify second node
        second_node = kg.nodes[1]
        assert second_node.type == NodeType.DOCUMENT
        assert second_node.properties['page_content'] == test_docs[1].page_content
        assert second_node.properties['document_metadata'] == test_docs[1].metadata


class TestKnowledgeGraphSaver:
    """Test cases for the KnowledgeGraphSaver component."""

    def test_component_initialization(self):
        """Test 1: Component initializes with correct default and custom paths."""
        # Test default initialization
        saver = KnowledgeGraphSaver()
        assert saver.default_output_path == "knowledge_graph.json"
        
        # Test custom initialization
        custom_path = "custom_kg.json"
        saver_custom = KnowledgeGraphSaver(output_path=custom_path)
        assert saver_custom.default_output_path == custom_path

    def test_successful_knowledge_graph_save(self):
        """Test 2: Component saves knowledge graph successfully."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test knowledge graph
            test_kg = KnowledgeGraph()
            test_node = Node(
                type=NodeType.DOCUMENT,
                properties={
                    "page_content": "Test content",
                    "document_metadata": {"source": "test.txt"}
                }
            )
            test_kg.nodes.append(test_node)
            
            # Mock the save method to avoid actual file operations during testing
            with patch.object(test_kg, 'save') as mock_save:
                mock_save.return_value = None
                
                output_path = os.path.join(temp_dir, "test_kg.json")
                saver = KnowledgeGraphSaver()
                result = saver.run(knowledge_graph=test_kg, output_path=output_path)
                
                # Verify results
                assert result['success'] is True
                assert result['saved_path'] == output_path
                
                # Verify save method was called with correct path
                mock_save.assert_called_once_with(output_path)

    def test_save_error_handling(self):
        """Test 3: Component handles save errors gracefully."""
        # Create a test knowledge graph
        test_kg = KnowledgeGraph()
        
        # Mock the save method to raise an exception
        with patch.object(test_kg, 'save') as mock_save:
            mock_save.side_effect = Exception("Simulated save error")
            
            saver = KnowledgeGraphSaver()
            result = saver.run(knowledge_graph=test_kg, output_path="invalid/path/test.json")
            
            # Verify error handling
            assert result['success'] is False
            assert result['saved_path'] == "invalid/path/test.json"
            
            # Verify save method was called (but failed)
            mock_save.assert_called_once_with("invalid/path/test.json")


class TestKnowledgeGraphIntegration:
    """Integration tests for knowledge graph components working together."""

    @patch('knowledge_graph_component.default_transforms')
    @patch('knowledge_graph_component.apply_transforms')
    @patch('knowledge_graph_component.LangchainLLMWrapper')
    @patch('knowledge_graph_component.LangchainEmbeddingsWrapper')
    @patch('knowledge_graph_component.ChatOpenAI')
    @patch('knowledge_graph_component.OpenAIEmbeddings')
    def test_generator_to_saver_pipeline(self, mock_embeddings, mock_chat, 
                                       mock_llm_wrapper, mock_emb_wrapper,
                                       mock_apply_transforms, mock_default_transforms):
        """Integration test: Generate knowledge graph and save it."""
        import tempfile
        
        # Setup mocks
        mock_chat.return_value = Mock()
        mock_embeddings.return_value = Mock()
        mock_llm_wrapper.return_value = Mock()
        mock_emb_wrapper.return_value = Mock()
        mock_default_transforms.return_value = []
        mock_apply_transforms.return_value = None
        
        # Create test document
        test_doc = LangChainDocument(
            page_content="Integration test content",
            metadata={"test": "integration"}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Generate knowledge graph
            generator = KnowledgeGraphGenerator(apply_transforms=False)
            gen_result = generator.run(documents=[test_doc])
            
            # Step 2: Save knowledge graph
            output_path = os.path.join(temp_dir, "integration_test.json")
            
            with patch.object(gen_result['knowledge_graph'], 'save') as mock_save:
                mock_save.return_value = None
                
                saver = KnowledgeGraphSaver()
                save_result = saver.run(
                    knowledge_graph=gen_result['knowledge_graph'], 
                    output_path=output_path
                )
                
                # Verify the complete pipeline worked
                assert gen_result['node_count'] == 1
                assert save_result['success'] is True
                assert save_result['saved_path'] == output_path


class TestDocumentToLangChainConverter:
    """Test cases for the DocumentToLangChainConverter component."""

    def test_successful_document_conversion(self):
        """Test 1: Component converts Haystack documents to LangChain format correctly."""
        # Create test Haystack documents
        haystack_docs = [
            HaystackDocument(
                content="This is test content 1",
                meta={"source": "test1.txt", "page": 1}
            ),
            HaystackDocument(
                content="This is test content 2",
                meta={"source": "test2.txt", "page": 2}
            )
        ]
        
        converter = DocumentToLangChainConverter()
        result = converter.run(documents=haystack_docs)
        
        # Verify conversion results
        assert result['document_count'] == 2
        assert len(result['langchain_documents']) == 2
        
        # Check first document
        first_doc = result['langchain_documents'][0]
        assert isinstance(first_doc, LangChainDocument)
        assert first_doc.page_content == "This is test content 1"
        assert first_doc.metadata == {"source": "test1.txt", "page": 1}
        
        # Check second document
        second_doc = result['langchain_documents'][1]
        assert second_doc.page_content == "This is test content 2"
        assert second_doc.metadata == {"source": "test2.txt", "page": 2}

    def test_empty_document_list_handling(self):
        """Test 2: Component handles empty document lists gracefully."""
        converter = DocumentToLangChainConverter()
        result = converter.run(documents=[])
        
        assert result['document_count'] == 0
        assert len(result['langchain_documents']) == 0
        assert result['langchain_documents'] == []

    def test_documents_with_missing_metadata(self):
        """Test 3: Component handles documents with missing or None metadata."""
        # Create documents with various metadata scenarios
        haystack_docs = [
            HaystackDocument(content="Content with metadata", meta={"key": "value"}),
            HaystackDocument(content="Content with None metadata", meta=None),
            HaystackDocument(content="Content with empty metadata", meta={})
        ]
        
        converter = DocumentToLangChainConverter()
        result = converter.run(documents=haystack_docs)
        
        # Verify all documents are converted
        assert result['document_count'] == 3
        assert len(result['langchain_documents']) == 3
        
        # Check metadata handling
        docs = result['langchain_documents']
        assert docs[0].metadata == {"key": "value"}  # Normal metadata
        assert docs[1].metadata == {}  # None converted to empty dict
        assert docs[2].metadata == {}  # Empty dict preserved


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic verification
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("Running basic test verification...")
        
        # Run basic tests without pytest
        generator_test = TestKnowledgeGraphGenerator()
        # Note: These tests require mocking which is complex without pytest
        # So we'll just verify the classes can be imported
        
        saver_test = TestKnowledgeGraphSaver()
        saver_test.test_component_initialization()
        
        converter_test = TestDocumentToLangChainConverter()
        converter_test.test_successful_document_conversion()
        converter_test.test_empty_document_list_handling()
        converter_test.test_documents_with_missing_metadata()
        
        print("Basic tests completed successfully!")
        print("For comprehensive testing, please install pytest: pip install pytest")