"""Shared configuration and LLM initialization."""
import os
from typing import Union
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=False)

def get_llm(
    model: str = None, 
    temperature: float = 0,
    max_retries: int = 2,
    timeout: int = 60
) -> Union[ChatOpenAI, ChatOllama]:
    """Get a configured LLM instance with automatic provider detection.
    
    Supports multiple LLM providers:
    - OpenAI: gpt-4, gpt-4-turbo, gpt-3.5-turbo, gpt-4o, gpt-4o-mini, etc.
    - Ollama: gpt-oss models (requires local Ollama server) 
    
    Args:
        model: Model name (defaults to OPENAI_MODEL env var or gpt-4o-mini)
        temperature: Temperature for generation (default: 0)
        max_retries: Maximum number of retries on failure (default: 2)
        timeout: Request timeout in seconds (default: 60)
        
    Returns:
        Configured LLM instance (ChatOpenAI, ChatOllama, or ChatAnthropic)
        
    Raises:
        ValueError: If model provider is not supported or API key is missing
        ImportError: If required provider library is not installed
    """
    if model is None:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
    # Attempt fallback to default OpenAI model
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError(
                    "Cannot fallback: OPENAI_API_KEY not found. "
                    "Please configure at least one LLM provider."
                )
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=openai_api_key,
                max_tokens=None,
                timeout=timeout,
                max_retries=max_retries,
            )
        except Exception as fallback_error:
            raise RuntimeError(
                f"Failed to initialize both requested model and fallback: {str(fallback_error)}"
            ) from e

        
    else:
    
        try:

            return ChatOllama(
                    model=model,  
                    temperature=temperature,
                    timeout=timeout,
                )
                
        except Exception as e:
            # Provide fallback with clear error message
            error_msg = (
                f"Failed to initialize model '{model}': {str(e)}\n"
                f"Falling back to default model 'gpt-4o-mini'"
            )
            print(f"WARNING: {error_msg}")
            
            
    
