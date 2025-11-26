"""V3 State definitions with enhanced error tracking and metadata."""
from typing import Dict, Any, Optional, Literal
from langgraph.graph import MessagesState
from pydantic import Field, field_validator
from shared.state import BaseClarificationDecision, BaseSupervisorDecision

# --- Enhanced Structured Outputs (Decision Models) ---

class ClarificationDecision(BaseClarificationDecision):
    """V3 enhanced clarification decision with better validation."""
    
    # Override fields with enhanced descriptions for V3 - must include type annotations
    need_clarification: bool = Field(
        description="True ONLY if absolutely critical info is missing (no business type or location hint)"
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="Specific, actionable question to ask user if clarification needed"
    )
    intent: Literal["general_chat", "business_search"] = Field(
        description="User's primary goal: casual conversation or business search"
    )
    search_query: Optional[str] = Field(
        default=None,
        description="Refined, specific search query (e.g., 'Italian restaurants', 'coffee shops')"
    )
    search_location: Optional[str] = Field(
        default=None,
        description="Complete location with city and state (e.g., 'Boston, MA')"
    )
    detail_level: Literal["general", "detailed", "reviews"] = Field(
        default="general",
        description="general=basic info, detailed=include websites, reviews=include sentiment"
    )
    
    @field_validator('clarification_question')
    def validate_clarification(cls, v, info):
        """Ensure clarification_question is provided when needed."""
        if info.data.get('need_clarification') and not v:
            raise ValueError("clarification_question required when need_clarification=True")
        return v

class SupervisorDecision(BaseSupervisorDecision):
    """V3 enhanced supervisor decision with reasoning and confidence."""
    
    # Override reasoning with enhanced description - must include type annotation
    reasoning: str = Field(description="Clear explanation of why this action was chosen")
    
    # V3-specific fields
    confidence: float = Field(
        ge=0.0, 
        le=1.0, 
        default=1.0,
        description="Confidence in this decision (0-1)"
    )
    should_finalize_early: bool = Field(
        default=False,
        description="True if we should finalize despite not having all requested data (e.g., API failures)"
    )

# --- Enhanced Graph State ---

class AgentState(MessagesState):
    """V3 State with enhanced error tracking and metadata."""
    # 'messages' is inherited from MessagesState
    
    # Structured Search Context
    search_query: str = ""
    search_location: str = ""
    detail_level: str = "general"
    
    # Pipeline Data (Full Output from 'search' for downstream tools)
    pipeline_data: Dict[str, Any] = {}
    
    # Structured Agent Outputs (v1 compatible)
    # This is the primary source of truth for the supervisor.
    # Format:
    # {
    #   "search": { 
    #       "success": True, 
    #       "result_count": 10,
    #       "metadata": {"execution_time_seconds": 2.3, "retry_count": 0}
    #   },
    #   "details": { "success": True, "document_count": 5 },
    #   "sentiment": { "success": False, "error": "API timeout", "error_type": "Timeout" }
    # }
    agent_outputs: Dict[str, Any] = {}
    
    # Enhanced Metadata for Debugging and Monitoring
    last_node_executed: Optional[str] = None
    execution_start_time: Optional[str] = None  # ISO format string for serialization
    total_error_count: int = 0
    retry_counts: Dict[str, int] = {}  # Track retries per tool
    consecutive_failures: Dict[str, int] = {}  # Track consecutive failures per tool
    
    # Final Output
    final_summary: str = ""
