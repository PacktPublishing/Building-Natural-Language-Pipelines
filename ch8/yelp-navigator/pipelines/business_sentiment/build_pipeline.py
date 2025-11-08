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

# Load environment variables
load_dotenv("../../.env")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")


def build_pipeline():
    """Build and return the Pipeline 3 instance."""
    # Initialize pipeline
    pipeline = Pipeline()
    
    # Initialize components
    parser = Pipeline1ResultParser()
    reviews_fetcher = YelpReviewsFetcher(
        api_key=RAPID_API_KEY,
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
    
    # Serialize the pipeline to YAML
    output_path = "pipeline3_reviews_sentiment.yaml"
    with open(output_path, "w") as file:
        pipeline.dump(file)
        
    print(f"\n✓ Pipeline serialized to: {output_path}")
    print("\nThe pipeline is now ready to be deployed with Hayhooks!")
