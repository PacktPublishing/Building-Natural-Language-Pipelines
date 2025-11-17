"""
Pipeline 1: Business Search with Named Entity Recognition

This script creates a Haystack pipeline that processes natural language queries 
to search for businesses on Yelp using Named Entity Recognition (NER).

Usage:
    python build_pipeline.py

Output:
    - pipeline1_business_search_ner.yaml (serialized pipeline)
"""

from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from haystack import Pipeline
from haystack.components.extractors import NamedEntityExtractor

# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import custom components from the components module
try:
    from .components import (
        QueryToDocument,
        EntityKeywordExtractor,
        YelpBusinessSearch
    )
except ImportError:
    # Fallback for when run as a script
    from pipelines.business_search.components import (
        QueryToDocument,
        EntityKeywordExtractor,
        YelpBusinessSearch
    )

# Load environment variables
load_dotenv("../../.env")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def build_pipeline():
    """Build and return the Pipeline 1 instance."""
    # Initialize pipeline
    pipeline = Pipeline()
    
    # Initialize components
    query_converter = QueryToDocument()
    ner_extractor = NamedEntityExtractor(backend="hugging_face", model="dslim/bert-base-NER")
    keyword_extractor = EntityKeywordExtractor()
    yelp_search = YelpBusinessSearch(api_key=RAPID_API_KEY)
    
    # Warm up the NER model (load into memory)
    print("Loading NER model...")
    ner_extractor.warm_up()
    print("✓ NER model loaded")
    
    # Add components to pipeline
    pipeline.add_component("query_converter", query_converter)
    pipeline.add_component("ner_extractor", ner_extractor)
    pipeline.add_component("keyword_extractor", keyword_extractor)
    pipeline.add_component("yelp_search", yelp_search)
    
    # Connect components
    pipeline.connect("query_converter.documents", "ner_extractor.documents")
    pipeline.connect("ner_extractor.documents", "keyword_extractor.documents")
    pipeline.connect("keyword_extractor.location", "yelp_search.location")
    pipeline.connect("keyword_extractor.keywords", "yelp_search.keywords")
    pipeline.connect("keyword_extractor.original_query", "yelp_search.original_query")
    
    print("✓ Pipeline built successfully")
    print("\nPipeline structure:")
    print("Query → QueryToDocument → NER → KeywordExtractor → YelpSearch → Results")
    
    return pipeline


if __name__ == "__main__":
    # Build the pipeline
    pipeline = build_pipeline()
    
    # draw pipeline
    pipeline.draw(path = f"pipeline1_business_search_ner.png")
    
    # Serialize the pipeline to YAML
    output_path = "pipeline1_business_search_ner.yaml"
    with open(output_path, "w") as file:
        pipeline.dump(file)
        
    print(f"\n✓ Pipeline serialized to: {output_path}")
    print("\nThe pipeline is now ready to be deployed with Hayhooks!")
