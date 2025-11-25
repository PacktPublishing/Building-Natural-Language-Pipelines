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
    Handle non-business chat queries with a welcoming message that redirects to business searches.
    
    Instead of answering general questions, this function returns a friendly welcome message
    that explains what the chatbot is designed for (business search and analysis) and prompts
    the user to ask about businesses.
    
    Args:
        state: Current agent state containing messages history
        track_errors: Whether to track errors (V3 feature). If True, returns
                     error tracking dict on failure.
    
    Returns:
        Tuple of (reply_content, error_tracking_dict)
        - reply_content: The welcome/redirect message
        - error_tracking_dict: None (no errors expected in simple message return)
    
    Example:
        # V2 usage (no error tracking)
        reply, _ = handle_general_chat(state, track_errors=False)
        
        # V3 usage (with error tracking)
        reply, error_info = handle_general_chat(state, track_errors=True)
    """
    # Return a friendly welcome message that redirects to business search functionality
    reply = """👋 Hello! I'm your Yelp Business Navigator assistant.

I'm specifically designed to help you:
• Search for businesses, restaurants, and services
• Analyze customer reviews and sentiment
• Provide detailed recommendations based on ratings and reviews
• Find contact information and websites for businesses

To get started, you can ask me things like:
- "Find Italian restaurants in Boston"
- "Show me coffee shops in Seattle with great reviews"
- "What are the best-rated Mexican restaurants in Austin?"
- "Find pizza places near San Francisco"

What type of business would you like to search for today?"""
    
    return reply, None
