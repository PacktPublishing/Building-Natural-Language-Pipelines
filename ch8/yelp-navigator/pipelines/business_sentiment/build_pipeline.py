"""
Pipeline 3: Business Reviews with Sentiment Analysis

This script creates a Haystack pipeline that fetches business reviews from Yelp
and performs sentiment analysis to identify highest and lowest rated reviews.

Usage:
    python build_pipeline.py

Output:
    - pipeline3_reviews_sentiment.yaml (serialized pipeline)
"""

from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from haystack import Pipeline

# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import custom components from the components module
try:
    from .components import (
        Pipeline1ResultParser,
        YelpReviewsFetcher,
        BatchSentimentAnalyzer,
        ReviewsAggregatorByBusiness
    )
except ImportError:
    # Fallback for when run as a script
    from pipelines.business_sentiment.components import (
        Pipeline1ResultParser,
        YelpReviewsFetcher,
        BatchSentimentAnalyzer,
        ReviewsAggregatorByBusiness
    )

# Load environment variables from multiple possible locations
env_paths = [".env", "../.env", "../../.env"]
for env_path in env_paths:
    if Path(env_path).exists():
        load_dotenv(env_path)
        break

RAPID_API_KEY = os.getenv("RAPID_API_KEY")

if not RAPID_API_KEY:
    print("⚠️  Warning: RAPID_API_KEY not found in environment variables")
    print("   The pipeline will try to load it from environment when running")


def build_pipeline():
    """Build and return the Pipeline 3 instance."""
    # Initialize pipeline
    pipeline = Pipeline()
    
    # Initialize components
    parser = Pipeline1ResultParser()
    # IMPORTANT: Always pass api_key=None to prevent exposing the key in the YAML file
    # The component will load it from RAPID_API_KEY environment variable at runtime
    reviews_fetcher = YelpReviewsFetcher(
        api_key=None,  # Never serialize the API key
        max_reviews_per_business=10
    )
    sentiment_analyzer = BatchSentimentAnalyzer()
    reviews_aggregator = ReviewsAggregatorByBusiness()
    
    # Warm up the sentiment analyzer
    print("Loading sentiment analysis model...")
    # The model is warmed up in BatchSentimentAnalyzer.__init__
    print("✓ Sentiment model loaded")
    
    # Add components to pipeline
    pipeline.add_component("parser", parser)
    pipeline.add_component("reviews_fetcher", reviews_fetcher)
    pipeline.add_component("sentiment_analyzer", sentiment_analyzer)
    pipeline.add_component("reviews_aggregator", reviews_aggregator)
    
    # Connect components
    pipeline.connect("parser.business_ids", "reviews_fetcher.business_ids")
    pipeline.connect("reviews_fetcher.documents", "sentiment_analyzer.documents")
    pipeline.connect("sentiment_analyzer.documents", "reviews_aggregator.documents")
    
    print("✓ Pipeline built successfully")
    print("\nPipeline structure:")
    print("Pipeline1Output → Parser → ReviewsFetcher → SentimentAnalyzer → ReviewsAggregator → Aggregated Documents")
    
    return pipeline


if __name__ == "__main__":
    # Build the pipeline
    pipeline = build_pipeline()
    
    # draw pipeline
    pipeline.draw(path = f"pipeline3_reviews_sentiment.png")
    
    # Serialize the pipeline to YAML
    output_path = "pipeline3_reviews_sentiment.yaml"
    with open(output_path, "w") as file:
        pipeline.dump(file)
        
    print(f"\n✓ Pipeline serialized to: {output_path}")
    print("\nThe pipeline is now ready to be deployed with Hayhooks!")
