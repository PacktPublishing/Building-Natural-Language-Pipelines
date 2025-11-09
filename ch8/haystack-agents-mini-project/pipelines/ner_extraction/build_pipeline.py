"""
Pipeline Building Script

This script demonstrates how to build complete Haystack pipelines by:
1. Initializing all required components
2. Creating a pipeline instance
3. Adding components to the pipeline
4. Connecting components in the correct order
5. Testing the pipeline

You will build three pipelines:
- Classification pipeline: Searches, fetches, cleans, and classifies articles
- NER pipeline: Searches, fetches, cleans, and extracts entities
- Combined pipeline: Searches, fetches, cleans, classifies, and extracts entities

TODO: Complete the pipeline building functions following the instructions.
"""

from haystack import Pipeline
from haystack.components.preprocessors import DocumentCleaner
from haystack.components.websearch import SearchApiWebSearch
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import HTMLToDocument
from haystack.utils import Secret
from components import EntityExtractor, NewsClassifier

# Import custom components from the components module
try:
    from .components import (
        EntityExtractor
    )
except ImportError:
    # Fallback for when run as a script
    from pipelines.classification.components import (
        EntityExtractor
    )


import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")


# ============================================================================
# Pipeline 1: Classification Pipeline
# ============================================================================

def build_classification_pipeline() -> Pipeline:
    """
    Build a pipeline that classifies web articles into categories.
    
    Pipeline flow:
    SearchApiWebSearch → LinkContentFetcher → HTMLToDocument → DocumentCleaner → NewsClassifier
    
    Returns:
        Configured Haystack Pipeline for classification
        
    TODO: Implement this function
    Steps:
    1. Create a Pipeline instance
    2. Initialize components:
       - SearchApiWebSearch (top_k=5, with API key, restricted to britannica.com)
       - LinkContentFetcher (retry_attempts=3, timeout=10)
       - HTMLToDocument
       - DocumentCleaner (remove_empty_lines=True, remove_extra_whitespaces=True)
       - NewsClassifier
    3. Add all components to the pipeline
    4. Connect components in order
    5. Return the pipeline
    """
    pipeline = Pipeline()
    
    # TODO: Initialize components
    # web_search = SearchApiWebSearch(
    #     top_k=5,
    #     api_key=Secret.from_env_var("SEARCH_API_KEY"),
    #     allowed_domains=["https://www.britannica.com/"]
    # )
    
    # TODO: Add more component initializations here
    
    # TODO: Add components to pipeline
    # pipeline.add_component(name='search', instance=web_search)
    # pipeline.add_component(name='fetcher', instance=...)
    # ... add remaining components
    
    # TODO: Connect components
    # pipeline.connect("search.links", "fetcher.urls")
    # pipeline.connect("fetcher", "htmldocument")
    # ... connect remaining components
    
    return pipeline

if __name__ == "__main__":
    # Build the pipeline
    pipeline = build_classification_pipeline()
    
    # Serialize the pipeline to YAML
    output_path = "classification_pipeline.yaml"
    with open(output_path, "w") as file:
        pipeline.dump(file)
        
    print(f"\n✓ Pipeline serialized to: {output_path}")
    print("\nThe pipeline is now ready to be deployed with Hayhooks!")