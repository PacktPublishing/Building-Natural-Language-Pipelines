"""V3 Prompts - uses shared prompts plus V3-specific enhancements."""
from shared.prompts import (
    summary_generation_prompt,
    base_clarification_prompt,
    state_aware_context_template,
    base_supervisor_instructions
)

def clarification_system_prompt_v3(current_query: str = "", current_location: str = "") -> str:
    """
    V3 State-aware clarification prompt with enhanced error context.
    Uses shared base components from shared/prompts.py.
    """
    # Only add the state context if we are in the middle of a search
    if current_query:
        return base_clarification_prompt + state_aware_context_template(current_query, current_location)
    else:
        return base_clarification_prompt


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

    base_prompt += base_supervisor_instructions
    base_prompt += """

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
