from typing import Annotated, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage
from operator import add


import operator
from typing import Annotated, List, Optional, Literal
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
    
    # Search Results Storage (Accumulated)
    raw_results: Annotated[List[str], operator.add] = [] 
    
    # Final Output
    final_summary: str = ""