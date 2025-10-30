#!/usr/bin/env python3
"""
Tests for warmup components from warmup_component.ipynb

These tests validate the functionality of custom Haystack components that use warm-up methods.
"""

import pytest
import numpy as np
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import List, Optional
from pathlib import Path

# Add the scripts directory to the Python path for imports
current_dir = Path(__file__).parent  # ch5/tests/
project_root = current_dir.parent    # ch5/
scripts_dir = project_root / "jupyter-notebooks" / "scripts"
sys.path.insert(0, str(scripts_dir))

from haystack import component, Document
from haystack.dataclasses import Document as HaystackDocument


# Recreate the components from the notebook for testing
@component
class LocalEmbedderText:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model: Optional[object] = None

    def warm_up(self):
        """
        Loads the SentenceTransformer model. This is called only once
        before the first run.
        """
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)

    @component.output_types(embeddings=List[List[float]])
    def run(self, texts: List[str]):
        """
        Embeds a list of texts using the pre-loaded model.
        """
        if self.model is None:
            raise RuntimeError("The model has not been loaded. Please call warm_up() before running.")
        
        embeddings = self.model.encode(texts).tolist()
        return {"embeddings": embeddings}


@component
class LocalEmbedderDocs:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model: Optional[object] = None

    def warm_up(self):
        """
        Loads the SentenceTransformer model. This is called only once
        before the first run.
        """
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)

    @component.output_types(embeddings=List[List[float]])
    def run(self, documents: List[Document]):
        """
        Embeds a list of texts using the pre-loaded model.
        """
        if self.model is None:
            raise RuntimeError("The model has not been loaded. Please call warm_up() before running.")

        texts = [doc.content for doc in documents]
        embeddings = self.model.encode(texts).tolist()
        return {"embeddings": embeddings}


class TestLocalEmbedderText:
    """Test cases for the LocalEmbedderText component."""

    def test_component_initialization(self):
        """Test 1: Component initializes correctly without loading model."""
        embedder = LocalEmbedderText()
        
        # Check initial state
        assert embedder.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert embedder.model is None  # Model should not be loaded yet
        
        # Test custom model name
        custom_embedder = LocalEmbedderText(model_name="custom-model")
        assert custom_embedder.model_name == "custom-model"
        assert custom_embedder.model is None

    @patch('sentence_transformers.SentenceTransformer')
    def test_warm_up_loads_model(self, mock_sentence_transformer):
        """Test 2: Warm-up method loads the model correctly and is idempotent."""
        # Setup mock
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        embedder = LocalEmbedderText()
        
        # Model should be None initially
        assert embedder.model is None
        
        # First warm_up should load the model
        embedder.warm_up()
        assert embedder.model is mock_model
        mock_sentence_transformer.assert_called_once_with("sentence-transformers/all-MiniLM-L6-v2")
        
        # Second warm_up should not reload the model (idempotent)
        embedder.warm_up()
        assert embedder.model is mock_model
        # Should still only be called once
        mock_sentence_transformer.assert_called_once()

    @patch('sentence_transformers.SentenceTransformer')
    def test_run_with_valid_texts(self, mock_sentence_transformer):
        """Test 3: Run method processes texts correctly after warm-up."""
        # Setup mock model
        mock_model = Mock()
        # Mock encode method to return numpy arrays (realistic behavior)
        mock_embeddings = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_model.encode.return_value = mock_embeddings
        mock_sentence_transformer.return_value = mock_model
        
        embedder = LocalEmbedderText()
        
        # Should raise error before warm-up
        with pytest.raises(RuntimeError, match="The model has not been loaded"):
            embedder.run(texts=["test text"])
        
        # Warm up the model
        embedder.warm_up()
        
        # Should work after warm-up
        test_texts = ["Hello world", "Testing embeddings"]
        result = embedder.run(texts=test_texts)
        
        # Verify results
        assert "embeddings" in result
        assert len(result["embeddings"]) == 2
        assert result["embeddings"] == mock_embeddings.tolist()
        
        # Verify model was called correctly
        mock_model.encode.assert_called_once_with(test_texts)


class TestLocalEmbedderDocs:
    """Test cases for the LocalEmbedderDocs component."""

    def test_component_initialization_with_documents(self):
        """Test 1: Document embedder initializes correctly."""
        embedder = LocalEmbedderDocs()
        
        # Check initial state
        assert embedder.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert embedder.model is None
        
        # Test with custom model
        custom_embedder = LocalEmbedderDocs(model_name="test-model")
        assert custom_embedder.model_name == "test-model"

    @patch('sentence_transformers.SentenceTransformer')
    def test_document_content_extraction(self, mock_sentence_transformer):
        """Test 2: Component correctly extracts content from Document objects."""
        # Setup mock model
        mock_model = Mock()
        mock_embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_model.encode.return_value = mock_embeddings
        mock_sentence_transformer.return_value = mock_model
        
        embedder = LocalEmbedderDocs()
        embedder.warm_up()
        
        # Create test documents
        test_docs = [
            HaystackDocument(content="First document content", meta={"source": "doc1"}),
            HaystackDocument(content="Second document content", meta={"source": "doc2"})
        ]
        
        result = embedder.run(documents=test_docs)
        
        # Verify that text extraction worked correctly
        expected_texts = ["First document content", "Second document content"]
        mock_model.encode.assert_called_once_with(expected_texts)
        
        # Verify embeddings structure
        assert "embeddings" in result
        assert len(result["embeddings"]) == 2

    @patch('sentence_transformers.SentenceTransformer')
    def test_empty_and_none_content_handling(self, mock_sentence_transformer):
        """Test 3: Component handles documents with missing or empty content."""
        # Setup mock model
        mock_model = Mock()
        mock_embeddings = np.array([[0.1, 0.2]])  # Only one embedding for one valid doc
        mock_model.encode.return_value = mock_embeddings
        mock_sentence_transformer.return_value = mock_model
        
        embedder = LocalEmbedderDocs()
        embedder.warm_up()
        
        # Create test documents with various content scenarios
        test_docs = [
            HaystackDocument(content="Valid content", meta={"source": "valid"}),
            HaystackDocument(content="", meta={"source": "empty"}),  # Empty content
            HaystackDocument(content=None, meta={"source": "none"})  # None content
        ]
        
        result = embedder.run(documents=test_docs)
        
        # Should only process the document with valid content
        expected_texts = ["Valid content"]  # Only non-empty content should be processed
        mock_model.encode.assert_called_once_with(expected_texts)


class TestWarmUpPatterns:
    """Test cases for warm-up patterns and best practices."""

    @patch('sentence_transformers.SentenceTransformer')
    def test_warm_up_idempotency(self, mock_sentence_transformer):
        """Test 1: Multiple warm_up calls don't reload the model."""
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        embedder = LocalEmbedderText()
        
        # Call warm_up multiple times
        embedder.warm_up()
        embedder.warm_up()
        embedder.warm_up()
        
        # Model should only be initialized once
        mock_sentence_transformer.assert_called_once()
        assert embedder.model is mock_model

    def test_error_before_warmup(self):
        """Test 2: Component raises clear error when used before warm-up."""
        embedder_text = LocalEmbedderText()
        embedder_docs = LocalEmbedderDocs()
        
        # Both should raise RuntimeError with clear message
        with pytest.raises(RuntimeError, match="The model has not been loaded"):
            embedder_text.run(texts=["test"])
            
        with pytest.raises(RuntimeError, match="The model has not been loaded"):
            embedder_docs.run(documents=[HaystackDocument(content="test")])

    @patch('sentence_transformers.SentenceTransformer')
    def test_warm_up_with_different_models(self, mock_sentence_transformer):
        """Test 3: Different model names are handled correctly during warm-up."""
        mock_model_1 = Mock()
        mock_model_2 = Mock()
        
        # Configure mock to return different models for different calls
        mock_sentence_transformer.side_effect = [mock_model_1, mock_model_2]
        
        # Create embedders with different models
        embedder_1 = LocalEmbedderText(model_name="model-1")
        embedder_2 = LocalEmbedderText(model_name="model-2")
        
        # Warm up both
        embedder_1.warm_up()
        embedder_2.warm_up()
        
        # Verify correct models were loaded
        assert embedder_1.model is mock_model_1
        assert embedder_2.model is mock_model_2
        
        # Verify correct model names were passed
        expected_calls = [
            ((("model-1",), {})),
            ((("model-2",), {}))
        ]
        assert mock_sentence_transformer.call_args_list == expected_calls


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic verification
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("Running basic test verification...")
        
        # Run basic tests without pytest
        text_embedder_test = TestLocalEmbedderText()
        text_embedder_test.test_component_initialization()
        
        docs_embedder_test = TestLocalEmbedderDocs()
        docs_embedder_test.test_component_initialization_with_documents()
        
        warmup_test = TestWarmUpPatterns()
        warmup_test.test_error_before_warmup()
        
        print("Basic tests completed successfully!")
        print("For comprehensive testing, please install pytest: pip install pytest")