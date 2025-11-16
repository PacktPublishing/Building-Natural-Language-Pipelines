"""Re-export shared prompts for backwards compatibility."""
from shared.prompts import (
    clarification_prompt,
    supervisor_approval_prompt,
    summary_generation_prompt
)

__all__ = [
    'clarification_prompt',
    'supervisor_approval_prompt',
    'summary_generation_prompt'
]
