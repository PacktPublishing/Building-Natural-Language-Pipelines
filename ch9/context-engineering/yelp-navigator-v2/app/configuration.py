import os
from dataclasses import dataclass, field, fields
from typing import Any, Optional
from langchain_core.runnables import RunnableConfig

@dataclass(kw_only=True)
class Configuration:
    """The configuration for the Yelp Navigator."""
    
    # Models
    model_name: str = "gpt-4o-mini"
    
    # Behavior
    allow_clarification: bool = True
    max_search_steps: int = 5  # Prevent infinite search loops
    
    @classmethod
    def from_runnable_config(cls, config: Optional[RunnableConfig] = None) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = config.get("configurable", {}) if config else {}
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
        }
        return cls(**{k: v for k, v in values.items() if v is not None})