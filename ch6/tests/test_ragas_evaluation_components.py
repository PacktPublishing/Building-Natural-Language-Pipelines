#!/usr/bin/env python3
"""
Tests for RAGAS evaluation components (ragasevalsupercomponent.py)

These tests validate the functionality of custom Haystack components for RAG evaluation using RAGAS.
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
sys.path.insert(0, str(scripts_dir / "ragas_evaluation"))

from haystack.dataclasses import Document as HaystackDocument
from haystack import Pipeline, SuperComponent


class TestCSVReaderComponent:
    """Test cases for the CSVReaderComponent."""
    
    def test_csv_reading_success(self):
        """Test 1: Component successfully reads a well-formatted CSV file."""
        from ragasevalsupercomponent import CSVReaderComponent
        
        # Create a temporary CSV file
        test_data = pd.DataFrame({
            'question': ['What is AI?', 'How does ML work?'],
            'ground_truth': ['AI is artificial intelligence', 'ML learns from data'],
            'contexts': ['["AI context"]', '["ML context"]']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            reader = CSVReaderComponent()
            result = reader.run(source=temp_path)
            
            assert isinstance(result['data_frame'], pd.DataFrame)
            assert len(result['data_frame']) == 2
            assert 'question' in result['data_frame'].columns
            assert 'ground_truth' in result['data_frame'].columns
            assert 'contexts' in result['data_frame'].columns
            
        finally:
            os.unlink(temp_path)
    
    def test_csv_reading_file_not_found(self):
        """Test 2: Component handles non-existent file gracefully."""
        from ragasevalsupercomponent import CSVReaderComponent
        
        reader = CSVReaderComponent()
        
        with pytest.raises(Exception):  # Should raise an appropriate exception
            reader.run(source="non_existent_file.csv")
    
    def test_csv_reading_empty_file(self):
        """Test 3: Component handles empty CSV file."""
        from ragasevalsupercomponent import CSVReaderComponent
        
        # Create an empty CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("question,ground_truth,contexts\n")  # Headers only
            temp_path = f.name
        
        try:
            reader = CSVReaderComponent()
            result = reader.run(source=temp_path)
            
            assert isinstance(result['data_frame'], pd.DataFrame)
            assert len(result['data_frame']) == 0
            
        finally:
            os.unlink(temp_path)


class TestRAGDataAugmenterComponent:
    """Test cases for the RAGDataAugmenterComponent."""
    
    def test_component_initialization(self):
        """Test 1: Component initializes correctly with a RAG SuperComponent."""
        from ragasevalsupercomponent import RAGDataAugmenterComponent
        
        # Create mock RAG SuperComponent
        mock_rag_sc = Mock(spec=SuperComponent)
        
        augmenter = RAGDataAugmenterComponent(rag_supercomponent=mock_rag_sc)
        
        assert augmenter.rag_supercomponent == mock_rag_sc
        assert "augmented_data_frame" in augmenter.output_names
    
    def test_data_augmentation_success(self):
        """Test 2: Component successfully augments evaluation data."""
        from ragasevalsupercomponent import RAGDataAugmenterComponent
        
        # Create mock RAG SuperComponent with predictable responses
        mock_rag_sc = Mock(spec=SuperComponent)
        mock_rag_sc.run.side_effect = [
            {
                "replies": ["AI is artificial intelligence"],
                "documents": [HaystackDocument(content="AI context document")]
            },
            {
                "replies": ["ML learns from data"],
                "documents": [HaystackDocument(content="ML context document")]
            }
        ]
        
        # Create test evaluation data
        test_data = pd.DataFrame({
            'question': ['What is AI?', 'How does ML work?'],
            'ground_truth': ['AI is artificial intelligence', 'ML learns from data']
        })
        
        augmenter = RAGDataAugmenterComponent(rag_supercomponent=mock_rag_sc)
        result = augmenter.run(data_frame=test_data)
        
        augmented_df = result['augmented_data_frame']
        
        # Verify the structure of augmented data
        assert isinstance(augmented_df, pd.DataFrame)
        assert len(augmented_df) == 2
        assert 'question' in augmented_df.columns
        assert 'ground_truth' in augmented_df.columns
        assert 'answer' in augmented_df.columns
        assert 'contexts' in augmented_df.columns
        
        # Verify the RAG SuperComponent was called for each question
        assert mock_rag_sc.run.call_count == 2
    
    def test_empty_dataframe_handling(self):
        """Test 3: Component handles empty input DataFrame."""
        from ragasevalsupercomponent import RAGDataAugmenterComponent
        
        mock_rag_sc = Mock(spec=SuperComponent)
        
        empty_data = pd.DataFrame(columns=['question', 'ground_truth'])
        
        augmenter = RAGDataAugmenterComponent(rag_supercomponent=mock_rag_sc)
        result = augmenter.run(data_frame=empty_data)
        
        augmented_df = result['augmented_data_frame']
        
        assert isinstance(augmented_df, pd.DataFrame)
        assert len(augmented_df) == 0
        assert mock_rag_sc.run.call_count == 0


class TestRagasEvaluationComponent:
    """Test cases for the RagasEvaluationComponent."""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_component_initialization(self):
        """Test 1: Component initializes correctly with default and custom parameters."""
        from ragasevalsupercomponent import RagasEvaluationComponent
        from haystack.components.generators import OpenAIGenerator
        from haystack.utils import Secret
        
        # Create mock generator
        mock_generator = Mock(spec=OpenAIGenerator)
        
        # Test default initialization
        evaluator = RagasEvaluationComponent(generator=mock_generator)
        assert hasattr(evaluator, 'ragas_llm')
        assert len(evaluator.metrics) == 4  # Default metrics count
        
        # Test custom initialization with custom metrics
        from ragas.metrics import Faithfulness
        evaluator_custom = RagasEvaluationComponent(
            generator=mock_generator,
            metrics=[Faithfulness()]
        )
        assert len(evaluator_custom.metrics) == 1
    
    def test_missing_generator_raises_error(self):
        """Test 2: Component requires a generator parameter."""
        from ragasevalsupercomponent import RagasEvaluationComponent
        
        with pytest.raises(TypeError):
            RagasEvaluationComponent()  # Should fail without generator
    
    @patch('ragasevalsupercomponent.evaluate')
    @patch('ragasevalsupercomponent.EvaluationDataset.from_pandas')
    @patch('ragasevalsupercomponent.HaystackLLMWrapper')
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_evaluation_success(self, mock_llm_wrapper, mock_eval_dataset, mock_evaluate):
        """Test 3: Component successfully evaluates augmented data."""
        from ragasevalsupercomponent import RagasEvaluationComponent
        from haystack.components.generators import OpenAIGenerator
        
        # Create mock generator
        mock_generator = Mock(spec=OpenAIGenerator)
        
        # Setup mocks
        mock_eval_dataset.return_value = Mock()
        mock_evaluate.return_value = Mock(scores={
            'faithfulness': 0.85,
            'factual_correctness': 0.80,
            'llm_context_recall': 0.75,
            'response_relevancy': 0.90
        })
        
        # Create test augmented data
        augmented_data = pd.DataFrame({
            'question': ['What is AI?'],
            'answer': ['AI is artificial intelligence'],
            'contexts': ['["AI is a field of computer science"]'],
            'ground_truth': ['AI is artificial intelligence']
        })
        
        evaluator = RagasEvaluationComponent(generator=mock_generator)
        result = evaluator.run(augmented_data_frame=augmented_data)
        
        # Verify evaluation was performed
        assert 'metrics' in result
        assert 'evaluation_df' in result
        mock_evaluate.assert_called_once()


class TestRAGEvaluationSuperComponent:
    """Test cases for the RAGEvaluationSuperComponent."""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_component_initialization(self):
        """Test 1: Component initializes correctly with a RAG SuperComponent."""
        from ragasevalsupercomponent import RAGEvaluationSuperComponent
        from haystack.components.generators import OpenAIGenerator
        
        # Create mock RAG SuperComponent and generator
        mock_rag_sc = Mock(spec=SuperComponent)
        mock_generator = Mock(spec=OpenAIGenerator)
        
        eval_sc = RAGEvaluationSuperComponent(
            rag_supercomponent=mock_rag_sc,
            system_name="Test_System",
            generator=mock_generator
        )
        
        assert eval_sc.rag_supercomponent == mock_rag_sc
        assert eval_sc.system_name == "Test_System"
        assert eval_sc.generator == mock_generator
        assert eval_sc.openai_api_key == "test-key"
        assert hasattr(eval_sc, 'pipeline')
        assert isinstance(eval_sc.pipeline, Pipeline)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_pipeline_components_added(self):
        """Test 2: Pipeline contains all expected components."""
        from ragasevalsupercomponent import RAGEvaluationSuperComponent
        from haystack.components.generators import OpenAIGenerator
        
        mock_rag_sc = Mock(spec=SuperComponent)
        mock_generator = Mock(spec=OpenAIGenerator)
        
        eval_sc = RAGEvaluationSuperComponent(
            rag_supercomponent=mock_rag_sc,
            system_name="Test_System",
            generator=mock_generator
        )
        
        # Check that all expected components are in the pipeline
        expected_components = ["reader", "augmenter", "evaluator"]
        
        for component_name in expected_components:
            assert component_name in eval_sc.pipeline.graph.nodes()
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_input_output_mappings(self):
        """Test 3: Input and output mappings are correctly configured."""
        from ragasevalsupercomponent import RAGEvaluationSuperComponent
        from haystack.components.generators import OpenAIGenerator
        
        mock_rag_sc = Mock(spec=SuperComponent)
        mock_generator = Mock(spec=OpenAIGenerator)
        
        eval_sc = RAGEvaluationSuperComponent(
            rag_supercomponent=mock_rag_sc,
            system_name="Test_System",
            generator=mock_generator
        )
        
        # Check input mappings
        assert "csv_source" in eval_sc.input_mapping
        assert "reader.source" in eval_sc.input_mapping["csv_source"]
        
        # Check output mappings
        assert "metrics" in eval_sc.output_mapping.values()
        assert "evaluation_df" in eval_sc.output_mapping.values()


class TestComparisonUtilities:
    """Test cases for comparison report utilities."""
    
    def test_create_comparison_report(self):
        """Test 1: Comparison report creation with mock results."""
        from ragasevalsupercomponent import create_comparison_report
        
        # Create mock evaluation results
        naive_results = {
            'metrics': Mock(scores={
                'faithfulness': 0.75,
                'factual_correctness': 0.70,
                'llm_context_recall': 0.65,
                'response_relevancy': 0.80
            }),
            'evaluation_df': pd.DataFrame({
                'question': ['Q1', 'Q2'],
                'faithfulness': [0.7, 0.8],
                'factual_correctness': [0.6, 0.8],
                'llm_context_recall': [0.6, 0.7],
                'response_relevancy': [0.8, 0.8]
            })
        }
        
        hybrid_results = {
            'metrics': Mock(scores={
                'faithfulness': 0.85,
                'factual_correctness': 0.80,
                'llm_context_recall': 0.75,
                'response_relevancy': 0.90
            }),
            'evaluation_df': pd.DataFrame({
                'question': ['Q1', 'Q2'],
                'faithfulness': [0.8, 0.9],
                'factual_correctness': [0.7, 0.9],
                'llm_context_recall': [0.7, 0.8],
                'response_relevancy': [0.9, 0.9]
            })
        }
        
        comparison_df = create_comparison_report(naive_results, hybrid_results)
        
        # Verify comparison report structure
        assert isinstance(comparison_df, pd.DataFrame)
        assert len(comparison_df) > 0
        assert 'Metric' in comparison_df.columns
        assert 'Naive RAG' in comparison_df.columns
        assert 'Hybrid RAG' in comparison_df.columns


def run_tests():
    """Run all tests in this module."""
    print("🧪 Running RAGAS Evaluation Component Tests")
    print("=" * 50)
    
    # Test CSVReaderComponent
    print("\n📄 Testing CSVReaderComponent...")
    csv_tests = TestCSVReaderComponent()
    try:
        csv_tests.test_csv_reading_success()
        csv_tests.test_csv_reading_file_not_found()
        csv_tests.test_csv_reading_empty_file()
        print("✅ CSVReaderComponent tests passed")
    except Exception as e:
        print(f"❌ CSVReaderComponent tests failed: {e}")
    
    # Test RAGDataAugmenterComponent
    print("\n📊 Testing RAGDataAugmenterComponent...")
    augmenter_tests = TestRAGDataAugmenterComponent()
    try:
        augmenter_tests.test_component_initialization()
        augmenter_tests.test_data_augmentation_success()
        augmenter_tests.test_empty_dataframe_handling()
        print("✅ RAGDataAugmenterComponent tests passed")
    except Exception as e:
        print(f"❌ RAGDataAugmenterComponent tests failed: {e}")
    
    # Test RagasEvaluationComponent
    print("\n📈 Testing RagasEvaluationComponent...")
    eval_tests = TestRagasEvaluationComponent()
    try:
        eval_tests.test_component_initialization()
        eval_tests.test_missing_api_key_raises_error()
        eval_tests.test_evaluation_success()
        print("✅ RagasEvaluationComponent tests passed")
    except Exception as e:
        print(f"❌ RagasEvaluationComponent tests failed: {e}")
    
    # Test RAGEvaluationSuperComponent
    print("\n🔗 Testing RAGEvaluationSuperComponent...")
    eval_sc_tests = TestRAGEvaluationSuperComponent()
    try:
        eval_sc_tests.test_component_initialization()
        eval_sc_tests.test_pipeline_components_added()
        eval_sc_tests.test_input_output_mappings()
        print("✅ RAGEvaluationSuperComponent tests passed")
    except Exception as e:
        print(f"❌ RAGEvaluationSuperComponent tests failed: {e}")
    
    # Test Comparison Utilities
    print("\n📋 Testing Comparison Utilities...")
    comp_tests = TestComparisonUtilities()
    try:
        comp_tests.test_create_comparison_report()
        print("✅ Comparison Utilities tests passed")
    except Exception as e:
        print(f"❌ Comparison Utilities tests failed: {e}")
    
    print("\n🎉 RAGAS Evaluation Component testing completed!")


if __name__ == "__main__":
    run_tests()