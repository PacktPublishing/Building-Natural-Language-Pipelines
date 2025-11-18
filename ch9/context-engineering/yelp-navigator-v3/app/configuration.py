import os
from dataclasses import dataclass, fields
from typing import Any, Optional
from langchain_core.runnables import RunnableConfig
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv(), override=False)  # Load environment variables from .env file

@dataclass(kw_only=True)
class Configuration:
    """The configuration for the Yelp Navigator V3 with memory support."""
    
    # Models
    model_name: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Behavior
    allow_clarification: bool = True
    max_search_steps: int = 5  # Prevent infinite search loops
    
    # Memory settings
    use_memory: bool = True  # Enable/disable memory caching
    memory_db_path: Optional[str] = None  # Path to SQLite database
    
    @classmethod
    def from_runnable_config(cls, config: Optional[RunnableConfig] = None) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = config.get("configurable", {}) if config else {}
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
        }
        return cls(**{k: v for k, v in values.items() if v is not None})
