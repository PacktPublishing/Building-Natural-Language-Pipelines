"""Memory-aware tools for interacting with Yelp data and business memory."""
from typing import Dict, Any, List, Optional
from .memory import BusinessMemory
from shared.tools import (
    chat_completion as shared_chat_completion,
    search_businesses as shared_search_businesses,
    get_business_details as shared_get_business_details,
    analyze_reviews_sentiment as shared_analyze_reviews_sentiment,
    BASE_URL
)

# Initialize the business memory
memory = BusinessMemory()

# Re-export chat_completion unchanged
chat_completion = shared_chat_completion


def search_businesses_with_memory(query: str) -> Dict[str, Any]:
    """
    Search for businesses and cache results in memory.
    
    This wraps the shared search_businesses tool and adds memory storage.
    """
    # Call the original search function
    result = shared_search_businesses.invoke({"query": query})
    
    if result.get("success") and result.get("businesses"):
        # Store each business in memory
        for business in result["businesses"]:
            memory.store_business(business)
        
        # Add memory metadata to result
        result["cached_business_ids"] = [b["id"] for b in result["businesses"]]
    
    return result


def get_business_details_with_memory(
    pipeline1_output: Dict[str, Any],
    business_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get detailed information about businesses, checking memory first.
    
    Args:
        pipeline1_output: Original pipeline output from search
        business_ids: Optional list of specific business IDs to get details for
                     If not provided, will get details for all businesses in pipeline output
    
    Returns:
        Dictionary with business details, using cached data when available
    """
    # If specific business IDs requested, check if we have them all in cache
    if business_ids:
        cached_details = []
        missing_ids = []
        
        for bid in business_ids:
            cached = memory.get_business_details(bid)
            if cached:
                # We have cached details
                basic_info = memory.get_business(bid)
                if basic_info:
                    cached_details.append({
                        "name": basic_info["name"],
                        "price_range": basic_info["price_range"],
                        "rating": basic_info["rating"],
                        "website_content_length": cached["website_content_length"],
                        "has_website_info": cached["has_website_info"],
                        "from_cache": True
                    })
            else:
                missing_ids.append(bid)
        
        # If we have everything cached, return it
        if not missing_ids and cached_details:
            return {
                "success": True,
                "document_count": len(cached_details),
                "businesses_with_details": cached_details,
                "from_cache": True
            }
    
    # Otherwise, call the API
    result = shared_get_business_details.invoke({"pipeline1_output": pipeline1_output})
    
    if result.get("success"):
        # Store details in memory
        # Extract business details from the full output
        full_output = result.get("full_output", {})
        documents = full_output.get("metadata_enricher", {}).get("documents", [])
        
        for doc in documents:
            meta = doc.get("meta", {})
            business_id = meta.get("business_id")
            
            if business_id:
                # Store the details
                memory.store_business_details(business_id, {
                    "website_content": doc.get("content", ""),
                    "has_website_info": len(doc.get("content", "")) > 0,
                    "website_content_length": len(doc.get("content", ""))
                })
        
        result["from_cache"] = False
    
    return result


def analyze_reviews_sentiment_with_memory(
    pipeline1_output: Dict[str, Any],
    business_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze reviews and sentiment, checking memory first.
    
    Args:
        pipeline1_output: Original pipeline output from search
        business_ids: Optional list of specific business IDs to analyze
    
    Returns:
        Dictionary with sentiment analysis, using cached data when available
    """
    # Check if we have cached sentiment for specific businesses
    if business_ids:
        cached_sentiment = []
        missing_ids = []
        
        for bid in business_ids:
            cached = memory.get_sentiment_data(bid)
            if cached:
                cached_sentiment.append({
                    "business_id": bid,
                    "total_reviews": cached["total_reviews"],
                    "sentiment_distribution": cached["sentiment_distribution"],
                    "overall_sentiment": cached["overall_sentiment"],
                    "positive_count": cached["sentiment_distribution"]["positive"],
                    "neutral_count": cached["sentiment_distribution"]["neutral"],
                    "negative_count": cached["sentiment_distribution"]["negative"],
                    "from_cache": True
                })
            else:
                missing_ids.append(bid)
        
        # If we have everything cached, return it
        if not missing_ids and cached_sentiment:
            return {
                "success": True,
                "business_count": len(cached_sentiment),
                "total_reviews_analyzed": sum(s["total_reviews"] for s in cached_sentiment),
                "sentiment_summaries": cached_sentiment,
                "from_cache": True
            }
    
    # Otherwise, call the API
    result = shared_analyze_reviews_sentiment.invoke({"pipeline1_output": pipeline1_output})
    
    if result.get("success"):
        # Store sentiment data in memory
        for summary in result.get("sentiment_summaries", []):
            business_id = summary.get("business_id")
            if business_id:
                memory.store_sentiment_data(business_id, summary)
        
        result["from_cache"] = False
    
    return result


def get_cached_business_info(business_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve all available cached information for a business.
    
    This is useful for answering follow-up questions without API calls.
    
    Returns:
        Dictionary with all cached data or None if business not in memory
    """
    basic = memory.get_business(business_id)
    if not basic:
        return None
    
    details = memory.get_business_details(business_id)
    sentiment = memory.get_sentiment_data(business_id)
    
    return {
        "business": basic,
        "details": details,
        "sentiment": sentiment,
        "has_details": details is not None,
        "has_sentiment": sentiment is not None
    }


def list_cached_businesses() -> List[Dict[str, Any]]:
    """Get a list of all businesses currently in memory."""
    return memory.get_all_cached_businesses()


# Export the memory-aware versions
__all__ = [
    'chat_completion',
    'search_businesses_with_memory',
    'get_business_details_with_memory',
    'analyze_reviews_sentiment_with_memory',
    'get_cached_business_info',
    'list_cached_businesses',
    'memory',
    'BASE_URL'
]
