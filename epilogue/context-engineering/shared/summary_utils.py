"""
Shared summary generation utilities for V1, V2, and V3 of yelp-navigator.

This module provides a unified function for generating summaries with optional
features for user question extraction and dual-message format support.
"""

from typing import Dict, Any, Optional, Callable
from langchain_core.messages import SystemMessage, HumanMessage


def generate_summary(
    state: Dict[str, Any],
    llm: Any,
    summary_prompt_func: Callable[..., Any],
    include_user_question: bool = False,
    use_dual_messages: bool = False
) -> str:
    """
    Generate summary using shared logic across all versions.
    
    This function provides a consistent interface for generating summaries
    with optional version-specific features:
    - V1: Basic summary generation with revision support
    - V2: Basic summary generation without revision
    - V3: Adds user question extraction and dual-message format
    
    Args:
        state: Current agent state dictionary
        llm: Language model instance to use for generation
        summary_prompt_func: Function to generate the summary prompt
            (e.g., summary_generation_prompt from shared.prompts)
        include_user_question: Whether to extract and include user question (V3 feature)
        use_dual_messages: Whether to use dual-message format (V3 feature)
            If True, includes both SystemMessage and HumanMessage for broader model compatibility
    
    Returns:
        str: The generated summary content
    
    Example:
        # V1 usage (minimal):
        summary = generate_summary(
            state=state,
            llm=llm,
            summary_prompt_func=summary_generation_prompt,
            include_user_question=False,
            use_dual_messages=False
        )
        
        # V3 usage (full features):
        summary = generate_summary(
            state=state,
            llm=llm,
            summary_prompt_func=summary_generation_prompt,
            include_user_question=True,
            use_dual_messages=True
        )
    """
    # Extract user question if requested (V3 feature)
    user_question = ""
    if include_user_question:
        messages = state.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, 'type') and msg.type == "human":
                user_question = msg.content
                break
    
    # Handle different state key names across versions
    # V1 uses "clarified_query" and "clarified_location"
    # V2/V3 use "search_query" and "search_location"
    search_query = state.get('search_query') or state.get('clarified_query', '')
    search_location = state.get('search_location') or state.get('clarified_location', '')
    
    # Generate the prompt using the provided prompt function
    prompt = summary_prompt_func(
        clarified_query=search_query,
        clarified_location=search_location,
        detail_level=state.get('detail_level', 'general'),
        agent_outputs=state.get('agent_outputs', {}),
        needs_revision=state.get("needs_revision", False),
        revision_feedback=state.get("revision_feedback", ""),
        user_question=user_question if include_user_question else ""
    )
    
    # Construct messages based on model compatibility requirements
    if use_dual_messages:
        # Some models require at least one non-system message for better compatibility
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content="Please generate the final summary based on the information provided.")
        ]
    else:
        # Most models work fine with just a system message
        messages = [SystemMessage(content=prompt)]
    
    # Invoke the LLM and return the response content
    response = llm.invoke(messages)
    return response.content
