"""V2 Prompts - uses shared base prompt components."""
from shared.prompts import (
    supervisor_approval_prompt,
    summary_generation_prompt,
    base_clarification_prompt,
    state_aware_context_template,
    base_supervisor_instructions
)

def clarification_system_prompt(current_query: str = "", current_location: str = "") -> str:
    """
    Generates a state-aware clarification prompt.
    It knows about the *previous* search to better handle follow-ups.
    """
    # Only add the state context if we are in the middle of a search
    if current_query:
        return base_clarification_prompt + state_aware_context_template(current_query, current_location)
    else:
        # If no current search, just use the base prompt for a new query
        return base_clarification_prompt

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
{base_supervisor_instructions}
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