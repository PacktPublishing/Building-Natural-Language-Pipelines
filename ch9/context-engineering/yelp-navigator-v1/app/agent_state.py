from typing import Annotated, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage
from operator import add


class AgentState(TypedDict):
    """State for the multi-agent system."""
    # Conversation tracking
    messages: Annotated[List[BaseMessage], add]
    
    # User intent
    user_query: str
    clarified_query: str  # What they're looking for (e.g., "Mexican food")
    clarified_location: str  # Where (e.g., "Austin, Texas")
    
    # Detail level: "general", "detailed", or "reviews"
    detail_level: str
    
    # Workflow control
    clarification_complete: bool
    next_agent: str  # Which agent to call next
    
    # Results from agents
    agent_outputs: Dict[str, Any]
    
    # Final output
    final_summary: str
    
    # Supervisor approval tracking
    approval_attempts: int  # Track how many times supervisor has reviewed
    needs_revision: bool  # Flag indicating if summary needs improvement
    revision_feedback: str  # What needs to be improved
