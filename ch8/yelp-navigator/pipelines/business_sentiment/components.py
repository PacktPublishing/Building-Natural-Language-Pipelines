"""
Custom components for Pipeline 3: Business Reviews with Sentiment Analysis

This module contains reusable custom components for fetching business reviews
from Yelp and performing sentiment analysis to identify highest and lowest rated reviews.
"""

import requests
from haystack import component, Document
from haystack.components.routers import TransformersTextRouter
from typing import List, Dict, Any
import logging
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@component
class Pipeline1ResultParser:
    """
    Parses the full Pipeline 1 output to extract business results.
    
    This component:
    1. Accepts the complete Pipeline 1 output dictionary
    2. Navigates the nested structure to find business results
    3. Extracts business IDs for downstream processing
    
    Input:
        - pipeline1_output (Dict): Complete output from Pipeline 1
    
    Output:
        - business_ids (List[str]): List of business IDs for review fetching
    """
    
    def __init__(self):
        """Initialize the component with a logger."""
        self.logger = logging.getLogger(__name__ + ".Pipeline1ResultParser")
    
    @component.output_types(business_ids=List[str])
    def run(self, pipeline1_output: Dict) -> Dict[str, List[str]]:
        """
        Parse Pipeline 1 output to extract business IDs.
        
        Args:
            pipeline1_output: Full output dictionary from Pipeline 1
                Expected structure: {'result': {'businesses': [...]}}
            
        Returns:
            Dictionary with business_ids key containing list of business IDs
        """
        self.logger.info("Parsing Pipeline 1 output")
        
        try:
            # Navigate the nested structure
            result = pipeline1_output.get('result', {})
            business_results = result.get('businesses', [])
            
            result_count = result.get('result_count', 0)
            extracted_location = result.get('extracted_location', '')
            extracted_keywords = result.get('extracted_keywords', [])
            
            # Extract business IDs (field name changed from bizId to business_id)
            business_ids = [business.get('business_id') for business in business_results if business.get('business_id')]
            
            self.logger.info(f"Extracted {len(business_ids)} business IDs from Pipeline 1")
            self.logger.debug(f"Result count: {result_count}, Location: {extracted_location}, Keywords: {extracted_keywords}")
            self.logger.debug(f"Business IDs: {business_ids}")
            
            return {"business_ids": business_ids}
            
        except Exception as e:
            self.logger.error(f"Error parsing Pipeline 1 output: {e}", exc_info=True)
            return {"business_ids": []}


@component
class YelpReviewsFetcher:
    """
    Fetches business reviews from Yelp API and creates Documents.
    
    This component:
    1. Accepts a list of business IDs
    2. Fetches reviews for each business
    3. Creates Haystack Documents with review text and metadata
    4. Returns documents ready for sentiment analysis
    
    Input:
        - business_ids (List[str]): List of Yelp business IDs
    
    Output:
        - documents (List[Document]): Documents containing review text and metadata
    """
    
    def __init__(self, api_key: str = None, max_reviews_per_business: int = 10):
        """
        Initialize the reviews fetcher.
        
        Args:
            api_key: RapidAPI key for Yelp Business Reviews API (loads from RAPID_API_KEY env var if not provided)
            max_reviews_per_business: Maximum reviews to fetch per business
        """
        # IMPORTANT: Store None instead of actual key to prevent serialization exposure
        # The actual key will be loaded at runtime in the run() method
        self.api_key = None  # Always store None to prevent YAML exposure
        self._runtime_api_key = api_key or os.getenv('RAPID_API_KEY')
        
        if not self._runtime_api_key:
            raise ValueError("API key must be provided or set in RAPID_API_KEY environment variable")
        
        self.base_url = "https://yelp-business-reviews.p.rapidapi.com/reviews"
        self.max_reviews = max_reviews_per_business
        self.headers = {
            "x-rapidapi-key": self._runtime_api_key,
            "x-rapidapi-host": "yelp-business-reviews.p.rapidapi.com"
        }
        self.logger = logging.getLogger(__name__ + ".YelpReviewsFetcher")
        
        # Rate limiting: delay between requests (in seconds)
        self.request_delay = 0.5  # 500ms between requests to avoid rate limits
    
    @component.output_types(documents=List[Document])
    def run(self, business_ids: List[str]) -> Dict[str, List[Document]]:
        """
        Fetch reviews and create Documents.
        
        Args:
            business_ids: List of business IDs to fetch reviews for
            
        Returns:
            Dictionary with 'documents' key containing review Documents
        """
        # Reload API key at runtime if not already set (for deserialized pipelines)
        if not hasattr(self, '_runtime_api_key') or not self._runtime_api_key:
            self._runtime_api_key = os.getenv('RAPID_API_KEY')
            if not self._runtime_api_key:
                raise ValueError("RAPID_API_KEY environment variable must be set")
            self.headers = {
                "x-rapidapi-key": self._runtime_api_key,
                "x-rapidapi-host": "yelp-business-reviews.p.rapidapi.com"
            }
            self.logger.info("Loaded API key from environment at runtime")
        
        self.logger.info(f"Fetching reviews for {len(business_ids)} businesses")
        all_documents = []
        successful_fetches = 0
        failed_fetches = 0
        
        for idx, biz_id in enumerate(business_ids):
            try:
                # Construct URL with business ID
                url = f"{self.base_url}/{biz_id}"
                
                self.logger.debug(f"Fetching reviews for business {idx+1}/{len(business_ids)}: {biz_id}")
                
                # Execute API request with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = requests.get(url, headers=self.headers, timeout=10)
                        
                        # Handle rate limiting
                        if response.status_code == 429:
                            retry_after = int(response.headers.get('Retry-After', 2))
                            self.logger.warning(f"Rate limit hit for {biz_id}, waiting {retry_after}s before retry {attempt+1}/{max_retries}")
                            time.sleep(retry_after)
                            continue
                        
                        # Handle authentication errors
                        if response.status_code == 401:
                            self.logger.error(f"Authentication failed for business {biz_id}. Check API key.")
                            failed_fetches += 1
                            break
                        
                        response.raise_for_status()
                        results = response.json()
                        
                        # Extract reviews
                        reviews = results.get('reviews', [])
                        self.logger.info(f"Fetched {len(reviews)} reviews for business {biz_id}")
                        
                        # Create documents for each review (up to max_reviews)
                        for i, review in enumerate(reviews[:self.max_reviews]):
                            doc = Document(
                                content=review.get('text', ''),
                                meta={
                                    "business_id": biz_id,
                                    "review_id": review.get('id', f"{biz_id}_{i}"),
                                    "rating": review.get('rating', 0),
                                    "user_name": review.get('user', {}).get('name', 'Anonymous'),
                                    "review_url": review.get('url', ''),
                                    "time_created": review.get('timeCreated', ''),
                                    "review_index": i
                                }
                            )
                            all_documents.append(doc)
                        
                        successful_fetches += 1
                        break  # Success, exit retry loop
                        
                    except requests.exceptions.RequestException as e:
                        if attempt == max_retries - 1:
                            self.logger.error(f"Failed to fetch reviews for {biz_id} after {max_retries} attempts: {e}")
                            failed_fetches += 1
                        else:
                            self.logger.warning(f"Request failed for {biz_id}, attempt {attempt+1}/{max_retries}: {e}")
                            time.sleep(1 * (attempt + 1))  # Exponential backoff
                
                # Add delay between requests to avoid rate limiting
                if idx < len(business_ids) - 1:  # Don't delay after last request
                    time.sleep(self.request_delay)
                    
            except Exception as e:
                self.logger.error(f"Unexpected error fetching reviews for business {biz_id}: {e}")
                failed_fetches += 1
                continue
        
        self.logger.info(f"Review fetching complete: {successful_fetches} successful, {failed_fetches} failed")
        self.logger.info(f"Successfully created {len(all_documents)} review documents")
        return {"documents": all_documents}


@component
class BatchSentimentAnalyzer:
    """
    Analyzes sentiment for multiple review documents in batch.
    
    This component wraps the sentiment router to process all documents
    and add sentiment metadata efficiently.
    
    Input:
        - documents (List[Document]): Review documents to analyze
    
    Output:
        - documents (List[Document]): Documents with sentiment metadata
    """
    
    def __init__(self, max_length: int = 500):
        """
        Initialize the batch sentiment analyzer.
        
        Args:
            max_length: Maximum number of characters to use for sentiment analysis
                       (model has a token limit of 514, roughly 500 chars is safe)
        """
        self.router = TransformersTextRouter(
            model="cardiffnlp/twitter-roberta-base-sentiment"
        )
        self.router.warm_up()
        
        self.sentiment_map = {
            "LABEL_0": "negative",
            "LABEL_1": "neutral",
            "LABEL_2": "positive"
        }
        self.max_length = max_length
        self.logger = logging.getLogger(__name__ + ".BatchSentimentAnalyzer")
    
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        """
        Analyze sentiment for all documents.
        
        Args:
            documents: List of review documents
            
        Returns:
            Dictionary with sentiment-enriched documents
        """
        # Handle None documents
        if documents is None:
            self.logger.warning("Received None for documents, using empty list")
            documents = []
            
        self.logger.info(f"Analyzing sentiment for {len(documents)} documents")
        enriched_docs = []
        
        for i, doc in enumerate(documents):
            try:
                # Handle None content
                content = doc.content if doc.content is not None else ""
                
                # Truncate text to max_length to avoid token limit errors
                truncated_text = content[:self.max_length] if len(content) > self.max_length else content
                
                if len(content) > self.max_length:
                    self.logger.debug(f"Truncated review {i+1} from {len(content)} to {self.max_length} chars")
                
                # Run sentiment analysis on truncated text
                result = self.router.run(text=truncated_text)
                
                # Extract the label from the result
                # The router outputs to different sockets (LABEL_0, LABEL_1, LABEL_2)
                sentiment_label = None
                for label in ["LABEL_0", "LABEL_1", "LABEL_2"]:
                    if label in result and result[label]:
                        sentiment_label = label
                        break
                
                # Map to human-readable sentiment
                sentiment = self.sentiment_map.get(sentiment_label, "unknown")
                
                # Create enriched document (keep original full content)
                enriched_doc = Document(
                    content=content,  # Keep original full content
                    meta={
                        **doc.meta,
                        "sentiment": sentiment,
                        "sentiment_label": sentiment_label
                    }
                )
                enriched_docs.append(enriched_doc)
                
            except Exception as e:
                self.logger.error(f"Error analyzing sentiment for document {i+1}: {e}")
                # Create document with unknown sentiment on error
                enriched_doc = Document(
                    content=doc.content if doc.content is not None else "",
                    meta={
                        **doc.meta,
                        "sentiment": "unknown",
                        "sentiment_label": None
                    }
                )
                enriched_docs.append(enriched_doc)
        
        self.logger.info(f"Sentiment analysis complete - enriched {len(enriched_docs)} documents")
        return {"documents": enriched_docs}


@component
class ReviewsAggregatorByBusiness:
    """
    Aggregates reviews by business and identifies top/bottom reviews.
    
    This component:
    1. Groups reviews by business ID
    2. Identifies highest-rated reviews (high star rating + positive sentiment)
    3. Identifies lowest-rated reviews (low star rating + negative sentiment)
    4. Creates summary documents for each business
    
    Input:
        - documents (List[Document]): All review documents with sentiment
    
    Output:
        - documents (List[Document]): One document per business with aggregated review metadata
    """
    
    def __init__(self):
        """Initialize the aggregator with a logger."""
        self.logger = logging.getLogger(__name__ + ".ReviewsAggregatorByBusiness")
    
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]) -> Dict[str, List[Document]]:
        """
        Aggregate reviews by business.
        
        Args:
            documents: List of review documents with sentiment metadata
            
        Returns:
            Dictionary with one document per business containing review summaries
        """
        # Handle None documents
        if documents is None:
            self.logger.warning("Received None for documents, using empty list")
            documents = []
            
        self.logger.info(f"Aggregating {len(documents)} reviews by business")
        
        # Group reviews by business_id
        business_reviews = {}
        
        for doc in documents:
            biz_id = doc.meta.get("business_id", "unknown")
            
            if biz_id not in business_reviews:
                business_reviews[biz_id] = []
            
            business_reviews[biz_id].append(doc)
        
        self.logger.info(f"Found reviews for {len(business_reviews)} businesses")
        
        # Create aggregated documents
        aggregated_docs = []
        
        for biz_id, reviews in business_reviews.items():
            # Separate by sentiment
            positive_reviews = [r for r in reviews if r.meta.get("sentiment") == "positive"]
            negative_reviews = [r for r in reviews if r.meta.get("sentiment") == "negative"]
            neutral_reviews = [r for r in reviews if r.meta.get("sentiment") == "neutral"]
            
            
            
            # Find highest-rated reviews (sort ALL positive reviews by rating)
            highest_rated = sorted(
                positive_reviews,  # Use the full list of positive reviews
                key=lambda x: x.meta.get("rating", 0), # Sort them by rating
                reverse=True # Highest rating (e.g., 5) comes first
            )[:3] # Take the top 3
            
            # Find lowest-rated reviews (sort ALL negative reviews by rating)
            lowest_rated = sorted(
                negative_reviews, # Use the full list of negative reviews
                key=lambda x: x.meta.get("rating", 0) # Sort them by rating
            )[:3] # Lowest rating (e.g., 1) comes first


            # Create summary content
            summary_content = f"Business Review Summary (ID: {biz_id}):\n"
            summary_content += f"Total Reviews: {len(reviews)}\n"
            summary_content += f"Positive: {len(positive_reviews)}, "
            summary_content += f"Neutral: {len(neutral_reviews)}, "
            summary_content += f"Negative: {len(negative_reviews)}"
            
            self.logger.debug(f"Business {biz_id}: {len(reviews)} total, "
                            f"{len(positive_reviews)} positive, "
                            f"{len(negative_reviews)} negative, "
                            f"{len(neutral_reviews)} neutral")
            
            # Create aggregated document
            agg_doc = Document(
                content=summary_content,
                meta={
                    "business_id": biz_id,
                    "total_reviews": len(reviews),
                    "positive_count": len(positive_reviews),
                    "neutral_count": len(neutral_reviews),
                    "negative_count": len(negative_reviews),
                    "highest_rated_reviews": [
                        {
                            "rating": r.meta.get("rating"),
                            "sentiment": r.meta.get("sentiment"),
                            "text": r.content,
                            "user": r.meta.get("user_name"),
                            "url": r.meta.get("review_url")
                        }
                        for r in highest_rated
                    ],
                    "lowest_rated_reviews": [
                        {
                            "rating": r.meta.get("rating"),
                            "sentiment": r.meta.get("sentiment"),
                            "text": r.content,
                            "user": r.meta.get("user_name"),
                            "url": r.meta.get("review_url")
                        }
                        for r in lowest_rated
                    ]
                }
            )
            aggregated_docs.append(agg_doc)
        
        self.logger.info(f"Created {len(aggregated_docs)} aggregated review documents")
        return {"documents": aggregated_docs}