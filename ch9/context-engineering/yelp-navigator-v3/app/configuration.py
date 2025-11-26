"""V3 Configuration with enhanced error handling, guardrails and retry settings."""
import os
from dataclasses import dataclass, fields
from typing import Any, Optional
from langchain_core.runnables import RunnableConfig
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=False)

@dataclass(kw_only=True)
class Configuration:
    """Enhanced configuration for V3 with guardrails support."""
    
    # Behavior
    allow_clarification: bool = True
    max_search_steps: int = 5  # Prevent infinite search loops
    
    # Error Handling & Retry Settings
    max_retry_attempts: int = 3
    retry_initial_interval: float = 1.0  # seconds
    retry_backoff_factor: float = 2.0
    retry_max_interval: float = 10.0  # max seconds between retries
    
    # Timeouts
    tool_timeout_seconds: int = 60
    
    # Monitoring
    log_token_usage: bool = False
    enable_detailed_logging: bool = True
    
    # === Minimal Guardrails ===
    # Simple checks integrated into clarify node
    enable_guardrails: bool = True
    sanitize_pii: bool = True  # Redact emails, phones, SSNs from context
    
    @classmethod
    def from_runnable_config(cls, config: Optional[RunnableConfig] = None) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = config.get("configurable", {}) if config else {}
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
        }
        return cls(**{k: v for k, v in values.items() if v is not None})

