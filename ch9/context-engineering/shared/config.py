"""Shared configuration and LLM initialization."""
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv(".env")

def get_llm(model: str = None, temperature: float = 0) -> ChatOpenAI:
    """Get a configured LLM instance.
    
    Args:
        model: Model name (defaults to OPENAI_MODEL env var or gpt-4o-mini)
        temperature: Temperature for generation (default: 0)
        
    Returns:
        Configured ChatOpenAI instance
    """
    if model is None:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    return ChatOpenAI(
        model=model,
        temperature=temperature
    )
