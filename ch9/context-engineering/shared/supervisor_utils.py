"""Shared supervisor utilities for V2 and V3.

This module provides unified supervisor decision-making logic that can be
shared across different versions with optional error handling and feature flags.
"""

from typing import Dict, Any, Callable, Optional, Tuple
from langchain_core.messages import SystemMessage, HumanMessage


def make_supervisor_decision(
    state: Dict[str, Any],
    llm: Any,
    supervisor_decision_model: type,
    prompt_generator: Callable,
    check_failures: bool = False,
    use_dual_messages: bool = False,
    max_consecutive_failures: int = 3
) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
    """
    Make supervisor decision using LLM with optional error handling.
    
    This function consolidates the supervisor logic from V2 and V3, with
    feature flags to enable V3-specific error handling when needed.
    
    Args:
        state: Current agent state containing search context and outputs
        llm: Language model instance to use for decision making
        supervisor_decision_model: The SupervisorDecision model class for structured output
        prompt_generator: Function that generates the supervisor prompt
            Should accept: (search_query, search_location, detail_level, 
                          has_search_data, has_details_data, has_sentiment_data,
                          error_context=None)
        check_failures: If True, enables V3-style error tracking and circuit breaker
        use_dual_messages: If True, uses both SystemMessage and HumanMessage (Gemini compatible)
        max_consecutive_failures: Maximum consecutive failures before circuit breaker triggers
    
    Returns:
        Tuple of (next_action, error_message, update_dict):
            - next_action: One of "search", "get_details", "analyze_sentiment", "finalize"
            - error_message: None if success, error string if should finalize early
            - update_dict: Optional dict with state updates (e.g., messages)
    """
    agent_outputs = state.get('agent_outputs', {})
    has_search_data = agent_outputs.get("search", {}).get("success", False)
    has_details_data = agent_outputs.get("details", {}).get("success", False)
    has_sentiment_data = agent_outputs.get("sentiment", {}).get("success", False)
    
    # V3 Feature: Check circuit breaker for consecutive failures
    if check_failures:
        consecutive_failures = state.get('consecutive_failures', {})
        
        # If any tool has failed too many times consecutively, finalize with what we have
        for tool_name, failure_count in consecutive_failures.items():
            if failure_count >= max_consecutive_failures:
                error_message = (
                    f"I apologize, but I'm experiencing persistent issues with the {tool_name} service. "
                    f"Let me provide you with the best information I can based on what's available."
                )
                return "finalize", error_message, None
        
        # Check for rate limiting or service unavailability
        rate_limited = False
        service_unavailable = False
        for tool_name, output in agent_outputs.items():
            if not output.get("success", True):
                if output.get("rate_limited", False):
                    rate_limited = True
                error_msg = output.get("error", "").lower()
                if "unavailable" in error_msg or "connection" in error_msg or "timeout" in error_msg:
                    service_unavailable = True
        
        # If rate limited or service unavailable, exit immediately
        if rate_limited or service_unavailable:
            error_type = "rate limit" if rate_limited else "service unavailability"
            error_message = (
                f"I apologize, but I'm unable to complete your request due to {error_type}. "
                f"The Yelp API service is currently unavailable or has rate limits in effect. "
                f"Please try again later."
            )
            return "finalize", error_message, None
    
    # Build error context for supervisor awareness (V3 feature)
    error_context = ""
    if check_failures:
        error_count = state.get("total_error_count", 0)
        if error_count > 0:
            error_details = []
            for tool_name, output in agent_outputs.items():
                if not output.get("success", True):
                    error_msg = output.get("error", "Unknown error")
                    retry_count = state.get("retry_counts", {}).get(tool_name, 0)
                    error_details.append(f"- {tool_name}: {error_msg} (retries: {retry_count})")
            
            if error_details:
                error_context = "Errors encountered:\n" + "\n".join(error_details)
    
    # Generate supervisor prompt
    prompt_kwargs = {
        'search_query': state['search_query'],
        'search_location': state['search_location'],
        'detail_level': state['detail_level'],
        'has_search_data': has_search_data,
        'has_details_data': has_details_data,
        'has_sentiment_data': has_sentiment_data
    }
    
    # Add error_context only if check_failures is enabled (V3)
    if check_failures:
        prompt_kwargs['error_context'] = error_context
    
    context = prompt_generator(**prompt_kwargs)
    
    # Create supervisor model with structured output
    supervisor_model = llm.with_structured_output(supervisor_decision_model)
    
    try:
        # Build messages based on compatibility mode
        if use_dual_messages:
            # V3: Use both system and human messages for broader model compatibility (Gemini)
            messages = [
                SystemMessage(content=context),
                HumanMessage(content="Please analyze the current state and decide the next action.")
            ]
        else:
            # V2: Use only system message
            messages = [SystemMessage(content=context)]
        
        # Invoke the model
        decision = supervisor_model.invoke(messages)
        
        # Debug logging (optional)
        if check_failures:
            print(f"Supervisor decision: {decision.next_action} "
                  f"(should_finalize_early: {getattr(decision, 'should_finalize_early', False)})")
        
        # Check if supervisor decides to finalize early (V3 feature)
        if check_failures and hasattr(decision, 'should_finalize_early') and decision.should_finalize_early:
            return "finalize", None, None
        
        # If decision is to finalize, return that
        if decision.next_action == "finalize":
            return "finalize", None, None
        
        return decision.next_action, None, None
        
    except Exception as e:
        # If supervisor fails, try to finalize with what we have
        error_msg = f"I encountered an issue coordinating the search: {str(e)}"
        
        # Build update dict with error tracking if enabled
        update_dict = None
        if check_failures:
            print(f"Supervisor error: {str(e)}")
            update_dict = {
                "total_error_count": state.get("total_error_count", 0) + 1
            }
        
        return "finalize", error_msg, update_dict


def get_node_mapping() -> Dict[str, str]:
    """
    Get the standard mapping from supervisor actions to graph nodes.
    
    Returns:
        Dict mapping supervisor action names to node names
    """
    return {
        "search": "search_tool",
        "get_details": "details_tool",
        "analyze_sentiment": "sentiment_tool",
        "finalize": "summary"
    }
