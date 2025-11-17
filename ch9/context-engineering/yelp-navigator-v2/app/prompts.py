# v2.zip/prompts.py
"""Re-export shared prompts for backwards compatibility."""
from shared.prompts import (
    supervisor_approval_prompt,
    summary_generation_prompt
)

def clarification_system_prompt(current_query: str = "", current_location: str = "") -> str:
    """
    Generates a state-aware clarification prompt.
    It knows about the *previous* search to better handle follow-ups.
    """
    
    # Base prompt from shared.zip/prompts.py
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

    When you have all information (or can make reasonable assumptions), respond EXACTLY in this format:
    CLARIFIED:
    QUERY: [what they're looking for]
    LOCATION: [where]
    DETAIL_LEVEL: [general/detailed/reviews]
    """
    
    # This is the new, state-aware part
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
        # If no current search, just use the base prompt for a new query
        return base_prompt

def supervisor_prompt(
    search_query: str, 
    search_location: str, 
    detail_level: str, 
    has_search_data: bool, 
    has_details_data: bool, 
    has_sentiment_data: bool
) -> str:
    """Generate the supervisor prompt for deciding next action."""
    return f"""You are a supervisor for a business search agent. Your goal is to gather the correct information to answer the user's request.

User Request:
- Goal: Find '{search_query}' in '{search_location}'.
- Target Detail Level: '{detail_level}'

Current Data We Have:
- Basic Search Results: {has_search_data}
- Website/Details Data: {has_details_data}
- Review/Sentiment Data: {has_sentiment_data}

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
"""

def summary_prompt(search_query: str, search_location: str, raw_results: list) -> str:
    """Generate the summary prompt for creating the final report."""
    # This prompt is used by the old summary_node. We are keeping the
    # v1-style summary_node, so this prompt is no longer used,
    # but we leave it here for reference.
    return f"""Generate a friendly summary for the user about {search_query} in {search_location}.
Use the following raw data:
{raw_results}
"""

__all__ = [
    'clarification_prompt',
    'clarification_system_prompt',
    'supervisor_approval_prompt',
    'summary_generation_prompt',
    'supervisor_prompt',
    'summary_prompt'
]