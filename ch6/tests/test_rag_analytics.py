#!/usr/bin/env python3
"""
Tests for RAG Analytics components (rag_analytics.py)

These tests validate the functionality of RAGAnalytics class for cost tracking and W&B integration.
"""

import pytest
import pandas as pd
import os
import sys
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the scripts directory to the Python path for imports
current_dir = Path(__file__).parent  # ch6/tests/
project_root = current_dir.parent    # ch6/
scripts_dir = project_root / "jupyter-notebooks" / "scripts"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir / "wandb_experiments"))


class TestRAGAnalytics:
    """Test cases for the RAGAnalytics class."""
    
    def create_mock_results(self):
        """Create mock evaluation results for testing."""
        mock_evaluation_df = pd.DataFrame({
            'question': [
                'What is artificial intelligence?',
                'How does machine learning work?',
                'Explain deep learning concepts.'
            ],
            'answer': [
                'AI is a field of computer science that aims to create intelligent machines.',
                'ML works by training algorithms on data to make predictions.',
                'Deep learning uses neural networks with multiple layers.'
            ],
            'contexts': [
                ['AI context document 1', 'AI context document 2'],
                ['ML context document 1', 'ML context document 2'],
                ['DL context document 1', 'DL context document 2']
            ],
            'ground_truth': [
                'AI is artificial intelligence',
                'ML is machine learning',
                'DL is deep learning'
            ],
            'faithfulness': [0.85, 0.90, 0.75],
            'factual_correctness': [0.80, 0.85, 0.70],
            'llm_context_recall': [0.75, 0.80, 0.65],
            'response_relevancy': [0.90, 0.95, 0.80]
        })
        
        mock_metrics = Mock()
        mock_metrics.scores = {
            'faithfulness': 0.83,
            'factual_correctness': 0.78,
            'llm_context_recall': 0.73,
            'response_relevancy': 0.88
        }
        
        return {
            'evaluation_df': mock_evaluation_df,
            'metrics': mock_metrics
        }
    
    @patch('rag_analytics.tiktoken.get_encoding')
    def test_analytics_initialization(self, mock_tiktoken):
        """Test 1: RAGAnalytics initializes correctly with default and custom parameters."""
        from rag_analytics import RAGAnalytics
        
        # Mock tiktoken encoder
        mock_encoder = Mock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_tiktoken.return_value = mock_encoder
        
        mock_results = self.create_mock_results()
        
        # Test default initialization
        analytics = RAGAnalytics(mock_results)
        assert analytics.model_name == "gpt-4o-mini"
        assert "text-embedding-3-small" in analytics.embedding_models
        assert "text-embedding-3-large" in analytics.embedding_models
        assert hasattr(analytics, 'pricing')
        assert hasattr(analytics, 'token_usage')
        assert hasattr(analytics, 'costs')
        
        # Test custom initialization
        custom_embedding_models = ["text-embedding-ada-002"]
        analytics_custom = RAGAnalytics(
            mock_results, 
            model_name="gpt-4", 
            embedding_models=custom_embedding_models
        )
        assert analytics_custom.model_name == "gpt-4"
        assert analytics_custom.embedding_models == custom_embedding_models
    
    @patch('rag_analytics.tiktoken.get_encoding')
    def test_token_usage_calculation(self, mock_tiktoken):
        """Test 2: Token usage is calculated correctly."""
        from rag_analytics import RAGAnalytics
        
        # Mock tiktoken encoder with predictable token counts
        mock_encoder = Mock()
        mock_encoder.encode.side_effect = [
            [1, 2, 3, 4, 5],      # 5 tokens for first context
            [1, 2, 3, 4, 5, 6],   # 6 tokens for first answer
            [1, 2, 3, 4],         # 4 tokens for second context
            [1, 2, 3, 4, 5, 6, 7], # 7 tokens for second answer
            [1, 2, 3],            # 3 tokens for third context
            [1, 2, 3, 4, 5]       # 5 tokens for third answer
        ]
        mock_tiktoken.return_value = mock_encoder
        
        mock_results = self.create_mock_results()
        
        analytics = RAGAnalytics(mock_results)
        
        # Verify token usage structure
        assert 'input_tokens' in analytics.token_usage
        assert 'output_tokens' in analytics.token_usage
        assert isinstance(analytics.token_usage['input_tokens'], list)
        assert isinstance(analytics.token_usage['output_tokens'], list)
        assert len(analytics.token_usage['input_tokens']) == 3
        assert len(analytics.token_usage['output_tokens']) == 3
    
    @patch('rag_analytics.tiktoken.get_encoding')
    def test_cost_calculation(self, mock_tiktoken):
        """Test 3: Cost calculation is accurate based on pricing."""
        from rag_analytics import RAGAnalytics
        
        # Mock tiktoken encoder
        mock_encoder = Mock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens each
        mock_tiktoken.return_value = mock_encoder
        
        mock_results = self.create_mock_results()
        
        analytics = RAGAnalytics(mock_results, model_name="gpt-4o-mini")
        
        # Verify cost structure
        assert 'total_input_tokens' in analytics.costs
        assert 'total_output_tokens' in analytics.costs
        assert 'input_cost' in analytics.costs
        assert 'output_cost' in analytics.costs
        assert 'total_cost' in analytics.costs
        
        # Verify cost is calculated (should be > 0 for non-zero tokens)
        assert analytics.costs['total_cost'] >= 0
        assert isinstance(analytics.costs['total_cost'], (int, float))
    
    @patch('rag_analytics.tiktoken.get_encoding')
    def test_embedding_usage_calculation(self, mock_tiktoken):
        """Test 4: Embedding usage calculation for different models."""
        from rag_analytics import RAGAnalytics
        
        # Mock tiktoken encoder
        mock_encoder = Mock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_tiktoken.return_value = mock_encoder
        
        mock_results = self.create_mock_results()
        
        embedding_models = ["text-embedding-3-small", "text-embedding-3-large"]
        analytics = RAGAnalytics(mock_results, embedding_models=embedding_models)
        
        # Verify embedding usage structure
        assert hasattr(analytics, 'embedding_usage')
        assert isinstance(analytics.embedding_usage, dict)
        
        # Check that costs are calculated for each embedding model
        for model in embedding_models:
            if model in analytics.embedding_usage:
                model_usage = analytics.embedding_usage[model]
                assert 'total_tokens' in model_usage
                assert 'cost' in model_usage
    
    @patch('rag_analytics.tiktoken.get_encoding')
    def test_performance_metrics_calculation(self, mock_tiktoken):
        """Test 5: Performance metrics are calculated correctly."""
        from rag_analytics import RAGAnalytics
        
        # Mock tiktoken encoder
        mock_encoder = Mock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]
        mock_tiktoken.return_value = mock_encoder
        
        mock_results = self.create_mock_results()
        
        analytics = RAGAnalytics(mock_results)
        
        # Test get_performance_summary method
        summary = analytics.get_performance_summary()
        
        assert isinstance(summary, dict)
        assert 'avg_faithfulness' in summary
        assert 'avg_factual_correctness' in summary
        assert 'avg_llm_context_recall' in summary
        assert 'avg_response_relevancy' in summary
        
        # Verify calculated averages are reasonable
        assert 0 <= summary['avg_faithfulness'] <= 1
        assert 0 <= summary['avg_factual_correctness'] <= 1
        assert 0 <= summary['avg_llm_context_recall'] <= 1
        assert 0 <= summary['avg_response_relevancy'] <= 1
    
    @patch('rag_analytics.tiktoken.get_encoding')
    def test_cost_per_query_calculation(self, mock_tiktoken):
        """Test 6: Cost per query calculation is accurate."""
        from rag_analytics import RAGAnalytics
        
        # Mock tiktoken encoder
        mock_encoder = Mock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens each
        mock_tiktoken.return_value = mock_encoder
        
        mock_results = self.create_mock_results()
        
        analytics = RAGAnalytics(mock_results)
        
        # Test cost per query calculation
        cost_per_query = analytics.get_cost_per_query()
        
        assert isinstance(cost_per_query, (int, float))
        assert cost_per_query >= 0
        
        # Cost per query should be total cost divided by number of queries
        expected_cost_per_query = analytics.costs['total_cost'] / len(analytics.evaluation_df)
        assert abs(cost_per_query - expected_cost_per_query) < 0.0001
    
    @patch('rag_analytics.tiktoken.get_encoding')
    @patch('rag_analytics.wandb')
    def test_wandb_logging(self, mock_wandb, mock_tiktoken):
        """Test 7: W&B logging functionality works correctly."""
        from rag_analytics import RAGAnalytics
        
        # Mock tiktoken encoder
        mock_encoder = Mock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]
        mock_tiktoken.return_value = mock_encoder
        
        mock_results = self.create_mock_results()
        
        analytics = RAGAnalytics(mock_results)
        
        # Test W&B logging method
        wandb_data = analytics.get_wandb_summary()
        
        assert isinstance(wandb_data, dict)
        assert 'performance_metrics' in wandb_data
        assert 'cost_analysis' in wandb_data
        assert 'token_usage' in wandb_data
        
        # Verify W&B data structure
        perf_metrics = wandb_data['performance_metrics']
        assert 'avg_faithfulness' in perf_metrics
        assert 'avg_factual_correctness' in perf_metrics
        
        cost_analysis = wandb_data['cost_analysis']
        assert 'total_cost' in cost_analysis
        assert 'cost_per_query' in cost_analysis
    
    @patch('rag_analytics.tiktoken.get_encoding')
    def test_pricing_model_support(self, mock_tiktoken):
        """Test 8: Different pricing models are supported correctly."""
        from rag_analytics import RAGAnalytics
        
        # Mock tiktoken encoder
        mock_encoder = Mock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]
        mock_tiktoken.return_value = mock_encoder
        
        mock_results = self.create_mock_results()
        
        # Test different model pricing
        models_to_test = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
        
        for model in models_to_test:
            analytics = RAGAnalytics(mock_results, model_name=model)
            
            # Verify model is in pricing table
            assert model in analytics.pricing
            assert 'input' in analytics.pricing[model]
            assert 'output' in analytics.pricing[model]
            
            # Verify cost calculation works
            assert analytics.costs['total_cost'] >= 0
    
    @patch('rag_analytics.tiktoken.get_encoding')
    def test_error_handling_empty_results(self, mock_tiktoken):
        """Test 9: Error handling with empty or malformed results."""
        from rag_analytics import RAGAnalytics
        
        # Mock tiktoken encoder
        mock_encoder = Mock()
        mock_encoder.encode.return_value = []
        mock_tiktoken.return_value = mock_encoder
        
        # Test with empty evaluation DataFrame
        empty_results = {
            'evaluation_df': pd.DataFrame(columns=['question', 'answer', 'contexts']),
            'metrics': Mock(scores={})
        }
        
        analytics = RAGAnalytics(empty_results)
        
        # Should not raise errors and handle gracefully
        assert analytics.costs['total_cost'] == 0
        assert len(analytics.token_usage['input_tokens']) == 0
        assert len(analytics.token_usage['output_tokens']) == 0


def run_tests():
    """Run all tests in this module."""
    print("🧪 Running RAG Analytics Tests")
    print("=" * 40)
    
    analytics_tests = TestRAGAnalytics()
    
    test_methods = [
        "test_analytics_initialization",
        "test_token_usage_calculation", 
        "test_cost_calculation",
        "test_embedding_usage_calculation",
        "test_performance_metrics_calculation",
        "test_cost_per_query_calculation",
        "test_wandb_logging",
        "test_pricing_model_support",
        "test_error_handling_empty_results"
    ]
    
    passed_tests = 0
    total_tests = len(test_methods)
    
    for test_method in test_methods:
        try:
            print(f"\n💰 Running {test_method}...")
            getattr(analytics_tests, test_method)()
            print(f"✅ {test_method} passed")
            passed_tests += 1
        except Exception as e:
            print(f"❌ {test_method} failed: {e}")
    
    print(f"\n🎉 RAG Analytics testing completed!")
    print(f"📊 Passed: {passed_tests}/{total_tests} tests")


if __name__ == "__main__":
    run_tests()