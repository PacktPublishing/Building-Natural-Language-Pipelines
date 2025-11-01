#!/usr/bin/env python3
"""
Tests for synthetic_test_components.py

These tests validate the functionality of custom Haystack components for synthetic test generation.
"""

import pytest
import pandas as pd
import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the scripts directory to the Python path for imports
current_dir = Path(__file__).parent  # ch5/tests/
project_root = current_dir.parent    # ch5/
scripts_dir = project_root / "jupyter-notebooks" / "scripts"
sys.path.insert(0, str(scripts_dir))

from haystack.dataclasses import Document as HaystackDocument
from langchain_core.documents import Document as LangChainDocument

from synthetic_data_generation.synthetic_test_components import (
    SyntheticTestGenerator,
    TestDatasetSaver
)


class TestSyntheticTestGenerator:
    """Test cases for the SyntheticTestGenerator component."""

    def test_component_initialization(self):
        """Test 1: Component initializes correctly with default and custom parameters."""
        # Test default initialization
        generator = SyntheticTestGenerator()
        assert generator.testset_size == 10
        assert generator.llm_model == "gpt-4o-mini"
        assert len(generator.query_distribution) == 3
        
        # Test custom initialization
        custom_distribution = [("single_hop", 1.0)]
        generator_custom = SyntheticTestGenerator(
            testset_size=20,
            llm_model="gpt-3.5-turbo",
            query_distribution=custom_distribution
        )
        assert generator_custom.testset_size == 20
        assert generator_custom.llm_model == "gpt-3.5-turbo"
        assert generator_custom.query_distribution == custom_distribution

    @patch('synthetic_test_components.TestsetGenerator')
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_fallback_generation_on_empty_documents(self, mock_testset_generator):
        """Test 2: Component handles empty document lists gracefully."""
        generator = SyntheticTestGenerator(testset_size=5)
        
        # Test with empty documents list
        result = generator.run(documents=[])
        
        assert result['success'] is False
        assert result['testset_size'] == 0
        assert result['generation_method'] == "none"
        assert isinstance(result['testset'], pd.DataFrame)
        assert len(result['testset']) == 0

    @patch('synthetic_test_components.TestsetGenerator')
    @patch('synthetic_test_components.llm_factory')
    @patch('synthetic_test_components.embedding_factory')
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_successful_generation_with_mock_data(self, mock_embedding, mock_llm, mock_testset_generator):
        """Test 3: Component generates test data successfully with valid inputs."""
        # Setup mocks
        mock_llm.return_value = Mock()
        mock_embedding.return_value = Mock()
        
        # Create mock testset
        mock_testset = Mock()
        mock_testset.to_pandas.return_value = pd.DataFrame({
            'question': ['What is AI?', 'How does ML work?'],
            'answer': ['AI is...', 'ML works by...'],
            'contexts': [['AI context'], ['ML context']],
            'ground_truth': ['AI truth', 'ML truth']
        })
        
        # Setup mock generator
        mock_generator_instance = Mock()
        mock_generator_instance.generate_with_langchain_docs.return_value = mock_testset
        mock_testset_generator.return_value = mock_generator_instance
        
        # Create test documents
        test_docs = [
            LangChainDocument(page_content="AI is artificial intelligence", metadata={}),
            LangChainDocument(page_content="ML is machine learning", metadata={})
        ]
        
        generator = SyntheticTestGenerator(testset_size=2)
        result = generator.run(documents=test_docs)
        
        assert result['success'] is True
        assert result['testset_size'] == 2
        assert result['generation_method'] == "documents"
        assert isinstance(result['testset'], pd.DataFrame)
        assert len(result['testset']) == 2


class TestTestDatasetSaver:
    """Test cases for the TestDatasetSaver component."""

    def test_component_initialization(self):
        """Test 1: Component initializes with correct default and custom paths."""
        # Test default initialization
        saver = TestDatasetSaver()
        assert saver.default_output_path == "synthetic_testset.csv"
        
        # Test custom initialization
        custom_path = "custom_test_data.csv"
        saver_custom = TestDatasetSaver(default_output_path=custom_path)
        assert saver_custom.default_output_path == custom_path

    def test_successful_csv_save(self):
        """Test 2: Component saves CSV files correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test data
            test_df = pd.DataFrame({
                'question': ['What is Python?', 'What is testing?'],
                'answer': ['Python is a language', 'Testing validates code'],
                'contexts': [['Python info'], ['Testing info']],
                'ground_truth': ['Python truth', 'Testing truth']
            })
            
            # Test saving
            output_path = os.path.join(temp_dir, "test_output.csv")
            saver = TestDatasetSaver()
            result = saver.run(testset=test_df, output_path=output_path, format="csv")
            
            # Verify results
            assert result['success'] is True
            assert result['row_count'] == 2
            assert result['saved_path'] == output_path
            assert os.path.exists(output_path)
            
            # Verify file content
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == 2
            assert 'question' in loaded_df.columns

    def test_json_format_support(self):
        """Test 3: Component supports JSON format saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test data
            test_df = pd.DataFrame({
                'question': ['What is JSON?'],
                'answer': ['JSON is a data format'],
                'contexts': [['JSON info']],
                'ground_truth': ['JSON truth']
            })
            
            # Test JSON saving
            output_path = os.path.join(temp_dir, "test_output.json")
            saver = TestDatasetSaver()
            result = saver.run(testset=test_df, output_path=output_path, format="json")
            
            # Verify results
            assert result['success'] is True
            assert result['row_count'] == 1
            assert os.path.exists(output_path)
            
            # Verify JSON content
            import json
            with open(output_path, 'r') as f:
                json_data = json.load(f)
            assert len(json_data) == 1
            assert json_data[0]['question'] == 'What is JSON?'


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic verification
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("Running basic test verification...")
        
        # Run basic tests without pytest
        generator_test = TestSyntheticTestGenerator()
        generator_test.test_component_initialization()
        
        saver_test = TestTestDatasetSaver()
        saver_test.test_component_initialization()
        saver_test.test_successful_csv_save()
        saver_test.test_json_format_support()
        
        print("Basic tests completed successfully!")