"""
Custom Haystack Components for Classification and NER Pipelines

This module contains custom components used in the multi-task NLP system:
- EntityExtractor: Extracts named entities and stores them in document metadata
- NewsClassifier: Classifies articles into predefined categories

TODO: Complete the implementation of these components following the exercise instructions.
"""

from haystack import component, Document
from haystack.components.extractors import NamedEntityExtractor
from haystack.components.routers import TransformersZeroShotTextRouter
from typing import List, Dict, Any



# ============================================================================
# Classification Component
# ============================================================================

# TODO: Initialize the zero-shot text router for classification
text_router = TransformersZeroShotTextRouter(
    model="MoritzLaurer/deberta-v3-large-zeroshot-v2.0",
    labels=["Politics", "Sport", "Technology", "Entertainment", "Business"]
)
text_router.warm_up()
# Hint: Use TransformersZeroShotTextRouter with model "MoritzLaurer/deberta-v3-large-zeroshot-v2.0"
# Labels: ["Politics", "Sport", "Technology", "Entertainment", "Business"]
# Don't forget to call warm_up()

text_router = None  # Replace with actual initialization


@component
class NewsClassifier:
    """
    Custom component that classifies documents into predefined categories.
    
    Uses zero-shot classification to categorize articles into one of:
    - Politics
    - Sport
    - Technology
    - Entertainment
    - Business
    
    The classification is stored in document.meta['labels'].
    
    Example usage:
        classifier = NewsClassifier()
        result = classifier.run(documents=[doc1, doc2])
        
        # Access classification
        for doc in result['documents']:
            category = doc.meta.get('labels')
            print(f"Article category: {category}")
    """
    
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Classify documents into categories.
        
        Args:
            documents: List of Haystack Document objects
            
        Returns:
            Dictionary with 'documents' key containing classified documents.
            Each document will have classification stored in document.meta['labels']
            
        Implementation steps:
        1. Loop through each document
        2. Get the document content
        3. Run classification using text_router
        4. Extract the top label from the results
        5. Store in document.meta['labels']
        6. Return the documents
        """
        # TODO: Implement classification logic
        # Hint: For each document:
        #   - text = document.content
        #   - labels = text_router.run(text)
        #   - Extract top label: top_label = list(labels.keys())[0]
        #   - Store: document.meta['labels'] = top_label
        
        return {"documents": documents}


if __name__ == "__main__":
    """
    Test the components individually before integrating into pipelines.
    """
    # TODO: Add test code here
    # Example:
    # test_doc = Document(content="Elon Musk announced new Tesla features in California.")
    # extractor = NewsClassifier()
    # result = extractor.run(documents=[test_doc])
    # print(result['documents'][0].meta.get('entities'))
    
    pass
