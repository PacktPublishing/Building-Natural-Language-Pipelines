from typing import Dict, Any
from langgraph.graph import MessagesState
from shared.state import BaseClarificationDecision, BaseSupervisorDecision

# --- Structured Outputs (Decision Models) ---
# V2 uses the base models directly from shared

class ClarificationDecision(BaseClarificationDecision):
    """V2 clarification decision - extends base model."""
    pass

class SupervisorDecision(BaseSupervisorDecision):
    """V2 supervisor decision - extends base model."""
    pass

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
