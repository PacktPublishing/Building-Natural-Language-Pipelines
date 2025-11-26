from typing import Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """State shared across all nodes in the workflow.
    
    Inherits 'messages: Annotated[List[BaseMessage], add_messages]' from MessagesState.
    """
    
    # User intent
    user_query: str
    clarified_query: str  # What they're looking for (e.g., "Mexican food")
    clarified_location: str  # Where (e.g., "Austin, Texas")
    
    # Detail level: "general", "detailed", or "reviews"
    # This determines the pipeline path after search
    detail_level: str
    
    # Workflow control
    clarification_complete: bool
    next_agent: str  # Only used by supervisor approval for revision routing
    
    # Node results
    agent_outputs: Dict[str, Any]  # Results from each node (search, details, sentiment)
    
    # Final output
    final_summary: str  # User-friendly response
    
    # Quality control (for Supervisor Approval Node)
    approval_attempts: int      # How many times supervisor has reviewed (max 2)
    needs_revision: bool        # True if summary needs improvement
    revision_feedback: str      # What to improve
