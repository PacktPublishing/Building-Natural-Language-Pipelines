"""Tools for interacting with Hayhooks pipelines."""

import requests
from typing import Dict, Any
from langchain_core.tools import tool


# Configuration - will be set by the notebook
BASE_URL = "http://localhost:1416"


def set_base_url(url: str):
    """Set the base URL for the Hayhooks server."""
    global BASE_URL
    BASE_URL = url


@tool
def search_businesses(query: str) -> Dict[str, Any]:
    """Search for businesses using natural language query."""
    try:
        print(f"[search_businesses] Calling API with query: {query}")
        response = requests.post(f"{BASE_URL}/business_search/run", json={"query": query}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            businesses = result.get('businesses', [])
            return {
                "success": True,
                "result_count": result.get('result_count', 0),
                "extracted_location": result.get('extracted_location', ''),
                "extracted_keywords": result.get('extracted_keywords', []),
                "businesses": [{
                    "id": b.get('id'), "name": b.get('name'), "rating": b.get('rating'),
                    "review_count": b.get('review_count'), "categories": b.get('categories', []),
                    "price_range": b.get('price_range', 'N/A'), "phone": b.get('phone', 'N/A'),
                    "location": b.get('location', {})
                } for b in businesses[:10]],
                "full_output": data
            }
        return {"success": False, "error": f"API returned status {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_business_details(pipeline1_output: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed information about businesses including website content."""
    try:
        response = requests.post(f"{BASE_URL}/business_details/run", json={"pipeline1_output": pipeline1_output}, timeout=60)
        if response.status_code == 200:
            data = response.json()
            documents = data.get('metadata_enricher', {}).get('documents', [])
            return {
                "success": True,
                "document_count": len(documents),
                "businesses_with_details": [{
                    "name": doc.get('meta', {}).get('business_name'),
                    "price_range": doc.get('meta', {}).get('price_range'),
                    "rating": doc.get('meta', {}).get('rating'),
                    "website_content_length": len(doc.get('content', '')),
                    "has_website_info": len(doc.get('content', '')) > 0
                } for doc in documents[:5]],
                "full_output": data
            }
        return {"success": False, "error": f"API returned status {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def analyze_reviews_sentiment(pipeline1_output: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze customer reviews and sentiment for businesses."""
    try:
        response = requests.post(f"{BASE_URL}/business_sentiment/run", json={"pipeline1_output": pipeline1_output}, timeout=120)
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            businesses = result.get('businesses', [])
            return {
                "success": True,
                "business_count": result.get('business_count', 0),
                "total_reviews_analyzed": result.get('total_reviews_analyzed', 0),
                "business_ids_processed": result.get('business_ids_processed', []),
                "sentiment_summaries": [{
                    "business_id": biz.get('business_id'),
                    "total_reviews": biz.get('total_reviews', 0),
                    "sentiment_distribution": biz.get('sentiment_distribution', {}),
                    "sentiment_percentages": biz.get('sentiment_percentages', {}),
                    "overall_sentiment": biz.get('overall_sentiment', 'unknown'),
                    "positive_count": biz.get('sentiment_distribution', {}).get('positive', 0),
                    "neutral_count": biz.get('sentiment_distribution', {}).get('neutral', 0),
                    "negative_count": biz.get('sentiment_distribution', {}).get('negative', 0),
                    "highest_rated_reviews": [{
                        "rating": review.get('rating'), "sentiment": review.get('sentiment'),
                        "text": review.get('text', '')[:200], "user": review.get('user')
                    } for review in biz.get('highest_rated_reviews', [])[:2]],
                    "lowest_rated_reviews": [{
                        "rating": review.get('rating'), "sentiment": review.get('sentiment'),
                        "text": review.get('text', '')[:200], "user": review.get('user')
                    } for review in biz.get('lowest_rated_reviews', [])[:2]]
                } for biz in businesses[:5]],
                "full_output": data
            }
        return {"success": False, "error": f"API returned status {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
