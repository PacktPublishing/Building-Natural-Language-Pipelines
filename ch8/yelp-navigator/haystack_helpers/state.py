from typing import List, Dict, Any
from pydantic import BaseModel, Field


# ===============================================================================
# 1. PYDANTIC STATE (The "Shared Memory")
# ===============================================================================

class YelpAgentState(BaseModel):
    """
    The shared state object passed between all components.
    Replicates the 'AgentState' TypedDict from LangGraph but with validation.
    """
    messages: List[str] = Field(default_factory=list)
    
    # User query fields
    user_query: str = ""
    clarified_query: str = ""
    clarified_location: str = ""
    detail_level: str = "general"  # general, detailed, reviews
    
    # Clarification state
    clarification_complete: bool = False
    clarification_attempts: int = 0
    
    # Agent outputs storage (matching LangGraph structure)
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Node results storage (deprecated, kept for compatibility)
    search_results: Dict[str, Any] = Field(default_factory=dict)
    details_results: Dict[str, Any] = Field(default_factory=dict)
    sentiment_results: Dict[str, Any] = Field(default_factory=dict)
    
    final_summary: str = ""
    
    # Supervisor State
    needs_revision: bool = False
    revision_feedback: str = ""
    approval_attempts: int = 0
    
    # Helper to append messages easily
    def add_message(self, msg: str):
        self.messages.append(msg)