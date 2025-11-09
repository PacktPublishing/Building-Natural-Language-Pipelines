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
# NER Component
# ============================================================================

# TODO: Initialize the NER model
# Hint: Use NamedEntityExtractor with the "dslim/bert-base-NER" model
# Don't forget to call warm_up() to load the model

ner_model = None  # Replace with actual initialization


@component
class EntityExtractor:
    """
    Custom component that extracts named entities from documents
    and stores them in document metadata.
    
    This component:
    - Processes a list of documents
    - Extracts named entities using a pre-trained NER model
    - Filters entities by confidence score
    - Organizes entities by type (PER, ORG, LOC, MISC)
    - Removes duplicates within each category
    - Stores results in document.meta['entities']
    
    Example usage:
        extractor = EntityExtractor(confidence_threshold=0.8)
        result = extractor.run(documents=[doc1, doc2])
        
        # Access entities
        for doc in result['documents']:
            entities = doc.meta.get('entities', {})
            print(f"People: {entities.get('PER', [])}")
            print(f"Organizations: {entities.get('ORG', [])}")
            print(f"Locations: {entities.get('LOC', [])}")
    """
    
    def __init__(self, confidence_threshold: float = 0.8):
        """
        Initialize the EntityExtractor.
        
        Args:
            confidence_threshold: Minimum confidence score for entity extraction (default: 0.8)
                                Only entities with scores above this threshold will be included.
        """
        # TODO: Store the confidence threshold
        self.confidence_threshold = confidence_threshold
    
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Extract entities from documents and store in metadata.
        
        Args:
            documents: List of Haystack Document objects to process
            
        Returns:
            Dictionary with 'documents' key containing enriched documents.
            Each document will have entities stored in document.meta['entities']
            as a dictionary with keys: PER, ORG, LOC, MISC
            
        Implementation steps:
        1. Loop through each document
        2. Get the document content
        3. Run NER extraction on the content using the ner_model
        4. Filter entities by confidence threshold
        5. Organize entities by type using sets for deduplication
        6. Convert sets to lists or comma-separated strings
        7. Store in document.meta['entities']
        8. Return the enriched documents
        """
        enriched_documents = []
        
        for document in documents:
            # TODO: Extract content from document
            content = document.content
            
            # TODO: Run NER extraction
            # Hint: Use ner_model.run(documents=[document])
            # This will add 'named_entities' to the document metadata
            
            # TODO: Initialize entity storage by type
            entities_by_type = {
                "LOC": set(),
                "PER": set(),
                "ORG": set(),
                "MISC": set()
            }
            
            # TODO: Get the named_entities from document metadata
            # Hint: named_entities = document.meta.get('named_entities', [])
            
            # TODO: Loop through extracted entities
            # For each entity:
            #   - Check if entity.score >= self.confidence_threshold
            #   - Extract the entity text: word = content[entity.start:entity.end]
            #   - Add to appropriate category: entities_by_type[entity.entity].add(word)
            
            # TODO: Convert sets to lists or comma-separated strings
            # Store in document.meta['entities']
            # Example: document.meta['entities'] = {
            #     "PER": list(entities_by_type["PER"]),
            #     "ORG": list(entities_by_type["ORG"]),
            #     ...
            # }
            
            enriched_documents.append(document)
        
        return {"documents": enriched_documents}




# ============================================================================
# Testing Code (Optional)
# ============================================================================

if __name__ == "__main__":
    """
    Test the components individually before integrating into pipelines.
    """
    # TODO: Add test code here
    # Example:
    # test_doc = Document(content="Elon Musk announced new Tesla features in California.")
    # extractor = EntityExtractor()
    # result = extractor.run(documents=[test_doc])
    # print(result['documents'][0].meta.get('entities'))
    
    pass
