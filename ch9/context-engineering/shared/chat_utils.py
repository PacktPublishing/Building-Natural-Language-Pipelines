"""Shared utilities for handling general chat interactions.

This module provides unified chat handling logic that can be used across
different versions (V2, V3) with optional error tracking features.
"""
from typing import Dict, Any, Optional, Tuple
from shared.tools import chat_completion


def handle_general_chat(
    state: Dict[str, Any],
    track_errors: bool = False
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Handle non-business chat queries using the chat completion endpoint.
    
    This function provides unified chat handling logic that converts LangChain
    messages to OpenAI format and processes the response appropriately.
    
    Args:
        state: Current agent state containing messages history
        track_errors: Whether to track errors (V3 feature). If True, returns
                     error tracking dict on failure.
    
    Returns:
        Tuple of (reply_content, error_tracking_dict)
        - reply_content: The assistant's response message
        - error_tracking_dict: Dict with error_count if track_errors=True and error occurred,
                              None otherwise
    
    Example:
        # V2 usage (no error tracking)
        reply, _ = handle_general_chat(state, track_errors=False)
        
        # V3 usage (with error tracking)
        reply, error_info = handle_general_chat(state, track_errors=True)
        if error_info:
            # Handle error tracking
            update_dict["total_error_count"] = state.get("total_error_count", 0) + error_info["error_count"]
    """
    def message_to_dict(msg):
        """Convert LangChain messages to OpenAI format."""
        if hasattr(msg, "type") and hasattr(msg, "content"):
            # Map LangChain message types to OpenAI roles
            role_mapping = {
                "human": "user",
                "ai": "assistant",
                "system": "system"
            }
            role = role_mapping.get(msg.type.lower(), "user")
            return {"role": role, "content": msg.content}
        if isinstance(msg, dict):
            return msg
        return {"role": "user", "content": str(msg)}
    
    try:
        # Convert conversation history to OpenAI message format
        messages = [message_to_dict(m) for m in state["messages"]]
        
        # Call the chat completion endpoint
        response = chat_completion.invoke({"messages": messages})
        
        # Extract the assistant's reply from the OpenAI-compatible response
        reply = None
        if response.get("success"):
            response_data = response.get("response", {})
            choices = response_data.get("choices", [])
            
            if choices and len(choices) > 0:
                # Extract content from the first choice's message
                message = choices[0].get("message", {})
                reply = message.get("content", "")
                
            if not reply:
                # Fallback if structure is unexpected
                reply = "I received a response but couldn't extract the content. Please try again."
        else:
            # Handle error case
            error_msg = response.get('error', 'Unknown error')
            reply = f"I encountered an error: {error_msg}. Please try again."
        
        # If we got a reply (even if it's an error message), return it without error tracking
        # since we successfully handled the request
        if reply and response.get("success"):
            return reply, None
        
        # If we couldn't get a successful response, track error if requested
        error_dict = {"error_count": 1} if track_errors else None
        return reply if reply else "I encountered an error. Please try again.", error_dict
        
    except Exception as e:
        # Unexpected exception
        reply = f"I encountered an unexpected error: {str(e)}. Please try again."
        error_dict = {"error_count": 1} if track_errors else None
        return reply, error_dict
