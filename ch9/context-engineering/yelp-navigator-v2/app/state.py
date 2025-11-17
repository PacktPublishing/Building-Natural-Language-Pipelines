from typing import Dict, Any

from typing import Optional, Literal
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

# --- Structured Outputs (Decision Models) ---

class ClarificationDecision(BaseModel):
    """Decides if we need to ask the user for more info or if we can proceed."""
    need_clarification: bool = Field(description="True if critical info (location, business type) is missing.")
    clarification_question: Optional[str] = Field(description="The question to ask the user if clarification is needed.")
    intent: Literal["general_chat", "business_search"] = Field(description="The user's goal.")
    search_query: Optional[str] = Field(description="Refined search query (e.g., 'Italian food').")
    search_location: Optional[str] = Field(description="Target location (e.g., 'Boston, MA').")
    detail_level: Literal["general", "detailed", "reviews"] = Field(default="general")

class SupervisorDecision(BaseModel):
    """Supervisor decides which tool to run next or if it's time to summarize."""
    next_action: Literal["search", "get_details", "analyze_sentiment", "finalize"]
    reasoning: str = Field(description="Why this action was chosen.")

# --- Graph State ---

class AgentState(MessagesState):
    """The state of the graph."""
    # 'messages' is inherited from MessagesState
    
    # Structured Search Context
    search_query: str = ""
    search_location: str = ""
    detail_level: str = "general"
    
    # Pipeline Data (Full Output from 'search' for downstream tools)
    pipeline_data: Dict[str, Any] = {}
    
    # Structured Agent Outputs (v1 compatible)
    # This is the primary source of truth for the supervisor.
    # It's a dictionary like:
    # {
    #   "search": { "success": True, "result_count": 10, ... },
    #   "details": { "success": True, "document_count": 5, ... },
    #   "sentiment": { "success": False, "error": "API timeout" }
    # }
    agent_outputs: Dict[str, Any] = {}
    
    # Final Output
    final_summary: str = ""
