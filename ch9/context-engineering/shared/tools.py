"""Shared tools for interacting with Hayhooks API endpoints."""
import requests
from typing import Dict, Any, List
from langchain_core.tools import tool

BASE_URL = "http://localhost:1416"

# Hayhooks Chat Completion Tool
@tool
def chat_completion(messages: List[Dict[str, str]], model: str = "gpt-4o-mini", stream: bool = False, base_url: str = BASE_URL) -> Dict[str, Any]:
    """Send a general chat completion request to the Hayhooks OpenAI-compatible endpoint.
    
    Args:
        messages: List of message dicts, e.g. [{"role": "user", "content": "Hello!"}]
        model: Model name to use (default: gpt-4o-mini)
        stream: Whether to stream the response (default: False)
        base_url: Base URL for the API endpoint
        
    Returns:
        Dictionary containing the chat completion response in OpenAI format:
        {
            "success": True/False,
            "response": {
                "id": "string",
                "object": "chat.completion",
                "created": int,
                "model": "string",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "string"
                        },
                        "finish_reason": "stop"
                    }
                ]
            },
            "error": "error message" (only if success is False)
        }
    """
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "stream": stream
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {"success": True, "response": data}
        else:
            error_msg = f"API returned status {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f": {error_detail}"
            except:
                error_msg += f": {response.text}"
            return {"success": False, "error": error_msg}
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out after 30 seconds"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": f"Could not connect to {base_url}. Is the server running?"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

@tool
def search_businesses(query: str, base_url: str = BASE_URL) -> Dict[str, Any]:
    """Search for businesses using natural language query.
    
    Args:
        query: Natural language search query (e.g., 'Mexican food in Austin, Texas')
        base_url: Base URL for the API endpoint
        
    Returns:
        Dictionary containing business search results with names, ratings, locations, etc.
    """
    try:
        response = requests.post(
            f"{base_url}/business_search/run",
            json={"query": query},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            
            # Extract key information for the agent
            businesses = result.get('businesses', [])
            return {
                "success": True,
                "result_count": result.get('result_count', 0),
                "extracted_location": result.get('extracted_location', ''),
                "extracted_keywords": result.get('extracted_keywords', []),
                "businesses": [
                    {
                        "name": b.get('name'),
                        "rating": b.get('rating'),
                        "review_count": b.get('review_count'),
                        "categories": b.get('categories', []),
                        "price_range": b.get('price_range', 'N/A'),
                        "phone": b.get('phone', 'N/A'),
                        "location": b.get('location', {})
                    }
                    for b in businesses[:10]  # Limit to first 10 for context
                ],
                "full_output": data  # Store full output for downstream pipelines
            }
        else:
            return {"success": False, "error": f"API returned status {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def get_business_details(pipeline1_output: Dict[str, Any], base_url: str = BASE_URL) -> Dict[str, Any]:
    """Get detailed information about businesses including website content.
    
    Args:
        pipeline1_output: Output from the search_businesses tool
        base_url: Base URL for the API endpoint
        
    Returns:
        Dictionary with enriched business details including website content
    """
    try:
        response = requests.post(
            f"{base_url}/business_details/run",
            json={"pipeline1_output": pipeline1_output},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get('metadata_enricher', {}).get('documents', [])
            
            return {
                "success": True,
                "document_count": len(documents),
                "businesses_with_details": [
                    {
                        "name": doc.get('meta', {}).get('business_name'),
                        "price_range": doc.get('meta', {}).get('price_range'),
                        "rating": doc.get('meta', {}).get('rating'),
                        "website_content_length": len(doc.get('content', '')),
                        "has_website_info": len(doc.get('content', '')) > 0
                    }
                    for doc in documents[:5]
                ],
                "full_output": data
            }
        else:
            return {"success": False, "error": f"API returned status {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool
def analyze_reviews_sentiment(pipeline1_output: Dict[str, Any], base_url: str = BASE_URL) -> Dict[str, Any]:
    """Analyze customer reviews and sentiment for businesses.
    
    Args:
        pipeline1_output: Output from the search_businesses tool
        base_url: Base URL for the API endpoint
        
    Returns:
        Dictionary with sentiment analysis and review summaries
    """
    try:
        response = requests.post(
            f"{base_url}/business_sentiment/run",
            json={"pipeline1_output": pipeline1_output},
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get('reviews_aggregator', {}).get('documents', [])
            
            return {
                "success": True,
                "analyzed_count": len(documents),
                "sentiment_summaries": [
                    {
                        "name": doc.get('meta', {}).get('business_name'),
                        "positive_count": doc.get('meta', {}).get('positive_count', 0),
                        "neutral_count": doc.get('meta', {}).get('neutral_count', 0),
                        "negative_count": doc.get('meta', {}).get('negative_count', 0),
                        "top_positive_reviews": doc.get('meta', {}).get('top_positive_reviews', [])[:2],
                        "bottom_negative_reviews": doc.get('meta', {}).get('bottom_negative_reviews', [])[:2]
                    }
                    for doc in documents[:5]
                ],
                "full_output": data
            }
        else:
            return {"success": False, "error": f"API returned status {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
