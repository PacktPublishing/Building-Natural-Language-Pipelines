"""Shared state models for Yelp Navigator V2 and V3."""
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator

# ============================================================================
# BASE DECISION MODELS (shared by V2 and V3)
# ============================================================================

class BaseClarificationDecision(BaseModel):
    """Base clarification decision model shared by V2 and V3."""
    need_clarification: bool = Field(
        description="True if critical info (location, business type) is missing."
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="The question to ask the user if clarification is needed."
    )
    intent: Literal["general_chat", "business_search"] = Field(
        description="The user's goal."
    )
    search_query: Optional[str] = Field(
        default=None,
        description="Refined search query (e.g., 'Italian food')."
    )
    search_location: Optional[str] = Field(
        default=None,
        description="Target location (e.g., 'Boston, MA'). MUST NOT be None - use 'United States' if unspecified."
    )
    detail_level: Literal["general", "detailed", "reviews"] = Field(
        default="general"
    )
    
    @model_validator(mode='after')
    def validate_location(self):
        """Ensure location is never None for business searches."""
        # Only validate if this is a business search (not general chat)
        if self.intent == 'business_search' and not self.search_location:
            self.search_location = "United States"  # Default fallback
        return self


class BaseSupervisorDecision(BaseModel):
    """Base supervisor decision model shared by V2 and V3."""
    next_action: Literal["search", "get_details", "analyze_sentiment", "finalize"]
    reasoning: str = Field(
        description="Why this action was chosen."
    )
