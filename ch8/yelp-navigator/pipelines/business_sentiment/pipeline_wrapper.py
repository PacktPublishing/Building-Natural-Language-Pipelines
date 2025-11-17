"""
Pipeline 3 Wrapper for Hayhooks

This wrapper loads the serialized Pipeline 3 (Business Reviews with Sentiment Analysis)
and provides API endpoints for use with Hayhooks.
"""

from typing import List, Dict, Any
import os
import sys
from pathlib import Path

from hayhooks import BasePipelineWrapper, log, get_last_user_message
from haystack import Pipeline

# Add parent directory to path for imports
current_dir = Path(__file__).parent
if str(current_dir.parent.parent) not in sys.path:
    sys.path.insert(0, str(current_dir.parent.parent))

# Import custom components from the components module
try:
    from .components import (
        Pipeline1ResultParser,
        YelpReviewsFetcher,
        BatchSentimentAnalyzer,
        ReviewsAggregatorByBusiness
    )
except ImportError:
    # Fallback for when loaded by hayhooks
    from pipelines.business_sentiment.components import (
        Pipeline1ResultParser,
        YelpReviewsFetcher,
        BatchSentimentAnalyzer,
        ReviewsAggregatorByBusiness
    )


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        """Initialize Pipeline 3: Business Reviews with Sentiment Analysis"""
        log.info("Setting up Pipeline 3: Business Reviews with Sentiment Analysis...")
        
        # Load the serialized pipeline
        pipeline_yaml = (Path(__file__).parent / "pipeline3_reviews_sentiment.yaml").read_text()
        self.pipeline = Pipeline.loads(pipeline_yaml)
        
        log.info("Pipeline 3 setup complete")
    
    def run_api(self, pipeline1_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch and analyze business reviews with sentiment analysis.
        
        This API endpoint:
        1. Accepts the complete Pipeline 1 output
        2. Extracts business IDs from the results
        3. Fetches reviews for each business from Yelp
        4. Performs sentiment analysis on all reviews
        5. Aggregates reviews by business and identifies highest/lowest rated
        6. Returns enriched documents with review insights
        
        Args:
            pipeline1_output: Complete output dictionary from Pipeline 1
            
        Returns:
            Dictionary with aggregated review documents and insights
        """
        log.info("Processing Pipeline 1 output for review sentiment analysis")
        
        try:
            # The pipeline1_output parameter already contains the data from the request
            # No need for extra nesting extraction - just pass it directly
            pipeline_inputs = {
                "parser": {"pipeline1_output": pipeline1_output}
            }
            
            log.info("Running Pipeline 3...")
            result = self.pipeline.run(
                pipeline_inputs,
                include_outputs_from={"parser", "reviews_fetcher", "sentiment_analyzer", "reviews_aggregator"}
            )
            
            # Extract results
            parser_output = result.get("parser", {})
            fetcher_output = result.get("reviews_fetcher", {})
            aggregator_output = result.get("reviews_aggregator", {})
            
            documents = aggregator_output.get("documents", [])
            business_ids = parser_output.get("business_ids", [])
            all_reviews = fetcher_output.get("documents", [])
            
            # Format the response
            response = {
                "business_count": len(documents),
                "business_ids_processed": business_ids,
                "total_reviews_analyzed": len(all_reviews),
                "businesses": [
                    {
                        "business_id": doc.meta.get("business_id"),
                        "total_reviews": doc.meta.get("total_reviews"),
                        "sentiment_distribution": {
                            "positive": doc.meta.get("positive_count"),
                            "neutral": doc.meta.get("neutral_count"),
                            "negative": doc.meta.get("negative_count")
                        },
                        "sentiment_percentages": {
                            "positive": round(doc.meta.get("positive_count", 0) / max(doc.meta.get("total_reviews", 1), 1) * 100, 1),
                            "neutral": round(doc.meta.get("neutral_count", 0) / max(doc.meta.get("total_reviews", 1), 1) * 100, 1),
                            "negative": round(doc.meta.get("negative_count", 0) / max(doc.meta.get("total_reviews", 1), 1) * 100, 1)
                        },
                        "overall_sentiment": (
                            "positive" if doc.meta.get("positive_count", 0) > doc.meta.get("negative_count", 0)
                            else "negative" if doc.meta.get("negative_count", 0) > doc.meta.get("positive_count", 0)
                            else "neutral"
                        ),
                        "highest_rated_reviews": doc.meta.get("highest_rated_reviews", []),
                        "lowest_rated_reviews": doc.meta.get("lowest_rated_reviews", [])
                    }
                    for doc in documents
                ],
                "raw_documents": documents  # Include full Document objects for downstream use
            }
            
            log.info(f"Pipeline 3 processed successfully - analyzed {len(all_reviews)} reviews for {len(documents)} businesses")
            return response
            
        except Exception as e:
            log.error(f"Error processing Pipeline 1 output: {str(e)}")
            return {
                "error": str(e),
                "business_count": 0,
                "businesses": []
            }
    
    def run_chat_completion(self, model: str, messages: list, body: dict) -> str:
        """
        OpenAI-compatible chat completion endpoint.
        
        This allows the pipeline to be used in chat interfaces by converting
        the review sentiment analysis results into a natural language response.
        """
        # For Pipeline 3, this would typically receive Pipeline 1 output
        # Since chat completion expects messages, we'll return a helpful message
        question = get_last_user_message(messages)
        
        return (
            "Pipeline 3 fetches business reviews from Yelp and performs sentiment analysis. "
            "To use this pipeline, pass the complete Pipeline 1 output to the run_api endpoint. "
            "This pipeline identifies highest-rated and lowest-rated reviews based on both "
            "star ratings and sentiment analysis, providing comprehensive review insights "
            "for each business."
        )


def extract_review_insights(documents: List[Any]) -> Dict[str, Any]:
    """
    Extract key insights from aggregated review documents.
    
    Utility function for downstream processing.
    
    Args:
        documents: List of aggregated review documents
    
    Returns:
        Dictionary with insights for each business
    """
    insights = {}
    
    for doc in documents:
        biz_id = doc.meta['business_id']
        total = doc.meta['total_reviews']
        
        if total == 0:
            continue
        
        insights[biz_id] = {
            "total_reviews": total,
            "sentiment_distribution": {
                "positive": doc.meta['positive_count'],
                "neutral": doc.meta['neutral_count'],
                "negative": doc.meta['negative_count']
            },
            "sentiment_percentages": {
                "positive": round(doc.meta['positive_count'] / total * 100, 1),
                "neutral": round(doc.meta['neutral_count'] / total * 100, 1),
                "negative": round(doc.meta['negative_count'] / total * 100, 1)
            },
            "overall_sentiment": (
                "positive" if doc.meta['positive_count'] > doc.meta['negative_count']
                else "negative" if doc.meta['negative_count'] > doc.meta['positive_count']
                else "neutral"
            ),
            "highest_rated_count": len(doc.meta['highest_rated_reviews']),
            "lowest_rated_count": len(doc.meta['lowest_rated_reviews'])
        }
    
    return insights
