"""Shared tools for interacting with Hayhooks API endpoints."""
import requests
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from .config import get_llm

BASE_URL = "http://localhost:1416"

MODEL = "gpt-oss:20b" #"gpt-4o-mini" #change to your preferred model 

# OpenAI Chat Completion Tool
@tool
def chat_completion(messages: List[Dict[str, str]], model: str = MODEL, stream: bool = False, base_url: str = BASE_URL) -> Dict[str, Any]:
    """Send a general chat completion request using OpenAI's chat completion API.
    
    Args:
        messages: List of message dicts, e.g. [{"role": "user", "content": "Hello!"}]
        model: Model name to use (default: MODEL constant, currently "gpt-oss:20b")
        stream: Whether to stream the response (default: False)
        base_url: Base URL for the API endpoint (deprecated, kept for compatibility)
        
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
    max_attempts = 3
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            # Get the LLM instance with error handling
            try:
                llm = get_llm(model=model)
            except Exception as llm_error:
                if attempt == max_attempts - 1:
                    return {
                        "success": False, 
                        "error": f"Failed to initialize model '{model}': {str(llm_error)}. Please check your API keys and model configuration."
                    }
                # Wait before retry (exponential backoff)
                import time
                time.sleep(2 ** attempt)
                continue
            
            # Add system instruction to always end with a summary
            system_instruction = SystemMessage(content=(
                "You are a helpful assistant for a Yelp business search and analysis system. "
                "After answering the user's question, ALWAYS end your response with a brief summary that includes:\n"
                "1. What this agentic system does (searches for businesses, analyzes reviews, and provides recommendations)\n"
                "2. What information it needs from users (location, business type/category, and specific preferences or requirements)"
            ))
            
            # Convert message dicts to LangChain message objects
            langchain_messages = [system_instruction]
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
                else:  # user or any other role
                    langchain_messages.append(HumanMessage(content=content))
            
            # Invoke the LLM with timeout protection
            try:
                response = llm.invoke(langchain_messages)
            except Exception as invoke_error:
                last_error = invoke_error
                if "rate limit" in str(invoke_error).lower() or "quota" in str(invoke_error).lower():
                    # Rate limit error - wait longer
                    if attempt < max_attempts - 1:
                        import time
                        wait_time = min(30, 5 * (2 ** attempt))
                        print(f"Rate limit hit, waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                elif "timeout" in str(invoke_error).lower():
                    # Timeout error - retry with shorter timeout
                    if attempt < max_attempts - 1:
                        import time
                        time.sleep(2)
                        continue
                raise  # Re-raise if not rate limit or last attempt
            
            # Format response in OpenAI-compatible format
            return {
                "success": True,
                "response": {
                    "id": getattr(response, "id", "chatcmpl-" + str(hash(response.content))),
                    "object": "chat.completion",
                    "created": int(getattr(response, "response_metadata", {}).get("created", 0)),
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response.content
                            },
                            "finish_reason": "stop"
                        }
                    ]
                },
                "metadata": {
                    "attempts": attempt + 1,
                    "model_used": model
                }
            }
            
        except Exception as e:
            last_error = e
            if attempt == max_attempts - 1:
                error_type = type(e).__name__
                error_details = str(e)
                
                # Provide helpful error messages based on error type
                if "api_key" in error_details.lower() or "authentication" in error_details.lower():
                    error_msg = f"Authentication failed for model '{model}': Check your API keys in .env file"
                elif "not found" in error_details.lower() or "does not exist" in error_details.lower():
                    error_msg = f"Model '{model}' not found. Available models depend on your provider."
                elif "connection" in error_details.lower() or "network" in error_details.lower():
                    error_msg = f"Network error connecting to {model}: Check your internet connection"
                else:
                    error_msg = f"Error in chat completion ({error_type}): {error_details}"
                
                return {
                    "success": False, 
                    "error": error_msg,
                    "error_type": error_type,
                    "attempts": max_attempts
                }
    
    # Should not reach here, but just in case
    return {
        "success": False, 
        "error": f"Failed after {max_attempts} attempts: {str(last_error)}",
        "attempts": max_attempts
    }

@tool
def search_businesses(query: str) -> Dict[str, Any]:
    """Search for businesses using natural language query."""
    try:
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
                    "location": b.get('location', {}), "website": b.get('website', 'N/A')
                } for b in businesses],
                "full_output": data
            }
        # Check for rate limiting
        if response.status_code == 429:
            return {"success": False, "error": "Rate limit exceeded", "rate_limited": True}
        return {"success": False, "error": f"API returned status {response.status_code}"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout - service may be unavailable"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error - service unavailable"}
    except Exception as e:
        error_msg = str(e)
        # Check if error message contains rate limit indicators
        if "429" in error_msg or "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
            return {"success": False, "error": "Rate limit exceeded", "rate_limited": True}
        return {"success": False, "error": error_msg}


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
                } for doc in documents],
                "full_output": data
            }
        if response.status_code == 429:
            return {"success": False, "error": "Rate limit exceeded", "rate_limited": True}
        return {"success": False, "error": f"API returned status {response.status_code}"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout - service may be unavailable"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error - service unavailable"}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
            return {"success": False, "error": "Rate limit exceeded", "rate_limited": True}
        return {"success": False, "error": error_msg}


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
                } for biz in businesses],
                "full_output": data
            }
        if response.status_code == 429:
            return {"success": False, "error": "Rate limit exceeded", "rate_limited": True}
        return {"success": False, "error": f"API returned status {response.status_code}"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout - service may be unavailable"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error - service unavailable"}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
            return {"success": False, "error": "Rate limit exceeded", "rate_limited": True}
        return {"success": False, "error": error_msg}

