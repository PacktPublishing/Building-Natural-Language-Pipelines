"""V3 Prompts - uses shared prompts plus V3-specific enhancements."""
from shared.prompts import summary_generation_prompt

def clarification_system_prompt_v3(current_query: str = "", current_location: str = "") -> str:
    """
    V3 State-aware clarification prompt with enhanced error context.
    Similar to V2 but with better handling for error scenarios.
    """
    
    base_prompt = """You are a helpful assistant that clarifies user requests for business searches.

Your goal is to extract three pieces of information:
1. QUERY: What type of business/food/service are they looking for?
2. LOCATION: Where are they searching?
3. DETAIL_LEVEL: What information do they need?
   - "general": Just basic business info (name, rating, location)
   - "detailed": Include website information and additional details
   - "reviews": Include customer reviews and sentiment analysis

Analyze the user's query and extract this information. If the query is too vague and missing critical information,
you should make reasonable assumptions and proceed rather than asking for clarification.

For example:
- If they say "restaurants" without a location, use "United States" as default
- If they don't specify detail level, use "general"
- If they mention wanting "reviews" or "what people say", use "reviews" detail level
"""
    
    # State-aware context for follow-up queries
    state_context = f"""
--- CURRENT SEARCH CONTEXT ---
You have already searched for:
- QUERY: "{current_query}"
- LOCATION: "{current_location}"

--- INSTRUCTIONS ---
Analyze the *latest user message* in the context of this CURRENT SEARCH.

1.  **If the user is asking for *more information* about the *same query*:**
    - Keep the QUERY and LOCATION the same (e.g., "{current_query}").
    - Update the DETAIL_LEVEL based on their request.
    - Example: If they ask "what do people say?" or "show me reviews", set DETAIL_LEVEL to "reviews".
    - Example: If they ask "does it have a website?", set DETAIL_LEVEL to "detailed".

2.  **If the user is asking for a *completely new search*:**
    - Extract the new QUERY and LOCATION.
    - Set DETAIL_LEVEL based on their new query (default to "general").
    
3.  **If the user is just chatting:**
    - Respond as a general chat. (The decision model will handle this).
    
Remember to use the user's *latest* message to make your decision.
"""

    # Only add the state context if we are in the middle of a search
    if current_query:
        return base_prompt + state_context
    else:
        return base_prompt


def supervisor_prompt_v3(
    search_query: str, 
    search_location: str, 
    detail_level: str, 
    has_search_data: bool, 
    has_details_data: bool, 
    has_sentiment_data: bool,
    error_context: str = ""
) -> str:
    """
    V3 Enhanced supervisor prompt with error awareness.
    
    Args:
        error_context: Information about any errors that occurred
    """
    base_prompt = f"""You are a supervisor for a business search agent. Your goal is to gather the correct information to answer the user's request.

User Request:
- Goal: Find '{search_query}' in '{search_location}'.
- Target Detail Level: '{detail_level}'

Current Data We Have:
- Basic Search Results: {has_search_data}
- Website/Details Data: {has_details_data}
- Review/Sentiment Data: {has_sentiment_data}
"""

    if error_context:
        base_prompt += f"""
⚠️ ERROR CONTEXT:
{error_context}

If errors have occurred, consider whether:
1. We have enough partial data to provide a useful response
2. We should retry the failed operation
3. We should finalize with what we have and inform the user of limitations
"""

    base_prompt += """
Instructions:
Based on the Target Detail Level and the Current Data We Have, decide the single next action.

1.  If 'Basic Search Results' is False, you MUST call 'search'. This is the first step.
2.  If 'Basic Search Results' is True, check the detail level:
    a.  If Detail Level is 'general': We have enough data. Call 'finalize'.
    b.  If Detail Level is 'detailed':
        - If 'Website/Details Data' is False, call 'get_details'.
        - If 'Website/Details Data' is True, we have enough data. Call 'finalize'.
    c.  If Detail Level is 'reviews':
        - If 'Review/Sentiment Data' is False, call 'analyze_sentiment'.
        - If 'Review/Sentiment Data' is True, we have enough data. Call 'finalize'.
        
IMPORTANT: Only call one action. Do not call 'get_details' or 'analyze_sentiment' if 'search' has not been run successfully.

If multiple errors have occurred and retries failed, consider setting should_finalize_early=True to provide
the best possible response with available data rather than continuing to fail.
"""
    
    return base_prompt


# Export both shared and v3-specific prompts
__all__ = [
    'clarification_system_prompt_v3',
    'supervisor_prompt_v3',
    'summary_generation_prompt',  # Re-exported from shared
]
