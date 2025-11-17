"""
Pipeline 2: Business Details with Website Content

This script creates a Haystack pipeline that processes Pipeline 1 business search 
results and creates enriched documents with website content for a document store.

Usage:
    python build_pipeline.py

Output:
    - pipeline2_business_details.yaml (serialized pipeline)
"""

from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from haystack import Pipeline
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import HTMLToDocument
from haystack.components.preprocessors import DocumentCleaner

# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import custom components from the components module
try:
    from .components import (
        Pipeline1ResultParser,
        WebsiteURLExtractor,
        DocumentMetadataEnricher
    )
except ImportError:
    # Fallback for when run as a script
    from pipelines.business_details.components import (
        Pipeline1ResultParser,
        WebsiteURLExtractor,
        DocumentMetadataEnricher
    )

# Load environment variables
load_dotenv("../../.env")


def build_pipeline():
    """Build and return the Pipeline 2 instance."""
    # Initialize pipeline
    pipeline = Pipeline()
    
    # Initialize components
    parser = Pipeline1ResultParser()
    url_extractor = WebsiteURLExtractor()
    content_fetcher = LinkContentFetcher(
        retry_attempts=2,
        timeout=10,
        raise_on_failure=False  # Don't fail pipeline if some websites timeout
    )
    html_converter = HTMLToDocument()
    document_cleaner = DocumentCleaner(
        remove_empty_lines=True,
        remove_extra_whitespaces=True,
        remove_substrings=['\n', '\r']
    )
    metadata_enricher = DocumentMetadataEnricher()
    
    # Add components to pipeline
    pipeline.add_component("parser", parser)
    pipeline.add_component("url_extractor", url_extractor)
    pipeline.add_component("content_fetcher", content_fetcher)
    pipeline.add_component("html_converter", html_converter)
    pipeline.add_component("document_cleaner", document_cleaner)
    pipeline.add_component("metadata_enricher", metadata_enricher)
    
    # Connect components
    pipeline.connect("parser.business_results", "url_extractor.business_results")
    pipeline.connect("url_extractor.urls", "content_fetcher.urls")
    pipeline.connect("content_fetcher.streams", "html_converter.sources")
    pipeline.connect("html_converter.documents", "document_cleaner.documents")
    pipeline.connect("document_cleaner.documents", "metadata_enricher.documents")
    pipeline.connect("url_extractor.business_metadata", "metadata_enricher.business_metadata")
    
    print("✓ Pipeline built successfully")
    print("\nPipeline structure:")
    print("Pipeline 1 Full Output → Parser → URLExtractor → ContentFetcher → HTMLConverter → DocumentCleaner → MetadataEnricher → Enriched Documents")
    
    return pipeline


if __name__ == "__main__":
    # Build the pipeline
    pipeline = build_pipeline()
    
    # draw pipeline
    pipeline.draw(path = f"pipeline2_business_details.png")
    
    # Serialize the pipeline to YAML
    output_path = "pipeline2_business_details.yaml"
    with open(output_path, "w") as file:
        pipeline.dump(file)
        
    print(f"\n✓ Pipeline serialized to: {output_path}")
    print("\nThe pipeline is now ready to be deployed with Hayhooks!")
