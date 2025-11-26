"""
Haystack-compatible State implementation for Yelp Navigator multi-agent system.

This module follows Haystack's official State pattern from:
haystack.components.agents.state.State

Key differences from the custom Pydantic implementation:
1. Uses Haystack's schema-based State class instead of Pydantic BaseModel
2. Messages field is automatically added (list[ChatMessage]) 
3. Handlers control merge behavior (merge_lists, replace_values)
4. Type validation and serialization built-in
"""

from typing import Dict, Any
from haystack.components.agents.state import State
from haystack.dataclasses import ChatMessage

# ===============================================================================
# 1. STATE SCHEMA DEFINITION (Following Haystack's Pattern)
# ===============================================================================

# Schema defines the structure of our agent's shared memory
# Each entry maps a parameter name to its type and optional handler
YELP_AGENT_STATE_SCHEMA = {
    # Primary Search Context
    "user_query": {"type": str},
    "clarified_query": {"type": str},
    "clarified_location": {"type": str},
    "detail_level": {"type": str},
    
    # Clarification state tracking
    "clarification_complete": {"type": bool},
    "clarification_attempts": {"type": int},
    
    # Tool Outputs (structured data from API calls)
    "agent_outputs": {"type": dict},
    "search_results": {"type": dict},
    "details_results": {"type": dict},
    "sentiment_results": {"type": dict},
    
    # Final output
    "final_summary": {"type": str},
    
    # Supervisor state
    "needs_revision": {"type": bool},
    "revision_feedback": {"type": str},
    "approval_attempts": {"type": int},
    
    # Note: 'messages' field with type list[ChatMessage] is automatically 
    # added by the State class, using merge_lists handler by default
}

# ===============================================================================
# 2. STATE FACTORY FUNCTION
# ===============================================================================

def create_yelp_state(user_query: str = "", **kwargs) -> State:
    """
    Factory function to create a Haystack State instance for Yelp Navigator.
    
    This uses Haystack's official State class which provides:
    - Schema validation
    - Automatic message field (list[ChatMessage])
    - Default handlers (merge_lists for lists, replace_values for others)
    - Serialization support (to_dict/from_dict)
    
    Args:
        user_query: Initial user search query
        **kwargs: Additional initial data to populate the state
        
    Returns:
        State: Initialized Haystack State object
        
    Example:
        >>> state = create_yelp_state("Find pizza in Chicago")
        >>> state.set("clarified_query", "pizza restaurants")
        >>> query = state.get("clarified_query")
    """
    # Prepare initial data with defaults
    initial_data = {
        "user_query": user_query,
        "clarified_query": "",
        "clarified_location": "",
        "detail_level": "general",
        "clarification_complete": False,
        "clarification_attempts": 0,
        "agent_outputs": {},
        "search_results": {},
        "details_results": {},
        "sentiment_results": {},
        "final_summary": "",
        "needs_revision": False,
        "revision_feedback": "",
        "approval_attempts": 0,
    }
    
    # Override with any provided kwargs
    initial_data.update(kwargs)
    
    # Create and return Haystack State instance
    return State(schema=YELP_AGENT_STATE_SCHEMA, data=initial_data)

# ===============================================================================
# 3. HELPER UTILITIES (Optional convenience functions)
# ===============================================================================

def add_message_to_state(state: State, message: str, role: str = "assistant") -> None:
    """
    Helper to add a ChatMessage to the state's messages field.
    
    The State class automatically merges list[ChatMessage] using merge_lists,
    so new messages are appended to the existing list.
    
    Args:
        state: The State instance to update
        message: The message text to add
        role: The role (user, assistant, system, tool)
    """
    chat_message = ChatMessage.from_assistant(message) if role == "assistant" else ChatMessage.from_user(message)
    current_messages = state.get("messages", [])
    state.set("messages", current_messages + [chat_message])

# ===============================================================================
