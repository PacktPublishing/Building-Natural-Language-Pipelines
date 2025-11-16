"""Re-export shared prompts for backwards compatibility."""
from shared.prompts import (
    clarification_prompt,
    supervisor_approval_prompt,
    summary_generation_prompt
)

# V2-specific prompts for the new architecture
clarification_system_prompt = clarification_prompt  # Alias for V2 naming

def supervisor_prompt(search_query: str, search_location: str, detail_level: str, raw_results: list) -> str:
    """Generate the supervisor prompt for deciding next action."""
    return f"""Goal: Find '{search_query}' in '{search_location}'.
Target Detail Level: {detail_level}

Current Results Log:
{raw_results}

Instructions:
1. If no results yet, call 'search'.
2. If we have results but need website info (and level is detailed/reviews), call 'get_details'.
3. If we have results but need opinions (and level is reviews), call 'analyze_sentiment'.
4. If we have sufficient info for the detail level, call 'finalize'.
"""

def summary_prompt(search_query: str, search_location: str, raw_results: list) -> str:
    """Generate the summary prompt for creating the final report."""
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
