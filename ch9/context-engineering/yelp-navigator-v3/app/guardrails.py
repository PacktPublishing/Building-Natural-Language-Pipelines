"""Minimal guardrails for V3.

Simple, lightweight checks that run within the clarify node:
1. Basic prompt injection pattern detection
2. PII sanitization (redact emails, phones, SSNs)

No separate node, no complex tracking, no LLM validation.
"""
import re
from typing import Optional, Tuple
from langchain_core.messages import HumanMessage

from .state import AgentState


# Simple prompt injection patterns (most critical)
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|all)\s+instructions?",
    r"system\s*:\s*you\s+are",
    r"forget\s+(everything|all)",
]

# PII patterns for sanitization
PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
}


def check_prompt_injection(content: str) -> Optional[str]:
    """Check for basic prompt injection patterns.
    
    Returns:
        Warning message if detected, None if safe
    """
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return "Please rephrase your question naturally."
    return None


def sanitize_pii(content: str) -> str:
    """Redact PII from content.
    
    Returns:
        Content with PII redacted
    """
    for pii_type, pattern in PII_PATTERNS.items():
        content = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', content)
    return content


def apply_guardrails(state: AgentState, enable_guardrails: bool = True, sanitize_pii_flag: bool = True) -> Tuple[AgentState, Optional[str]]:
    """Apply minimal guardrails to state.
    
    Args:
        state: Current agent state
        enable_guardrails: Enable prompt injection check
        sanitize_pii_flag: Enable PII sanitization
    
    Returns:
        (updated_state, warning_message)
        warning_message is set if a violation is detected
    """
    messages = state.get("messages", [])
    if not messages:
        return state, None
    
    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return state, None
    
    content = str(last_message.content)
    
    # Check for prompt injection
    if enable_guardrails:
        warning = check_prompt_injection(content)
        if warning:
            print(f"[GUARDRAIL] Prompt injection detected: {content[:50]}...")
            return state, warning
    
    # Sanitize PII
    if sanitize_pii_flag:
        sanitized_content = sanitize_pii(content)
        if sanitized_content != content:
            print(f"[GUARDRAIL] PII detected and sanitized")
            print(f"  Original: {content[:100]}")
            print(f"  Sanitized: {sanitized_content[:100]}")
            # Create new message with sanitized content
            new_message = HumanMessage(content=sanitized_content)
            new_messages = messages[:-1] + [new_message]
            # Return updated state with new messages
            updated_state = dict(state)
            updated_state["messages"] = new_messages
            return updated_state, None
    
    return state, None
