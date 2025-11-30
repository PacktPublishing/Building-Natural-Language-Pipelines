"""Shared configuration and LLM initialization."""
import os
from typing import Union
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=False)

def get_llm(
    model: str = None, 
    temperature: float = None,
    max_retries: int = 2,
    timeout: int = 120
) -> Union[ChatOpenAI, ChatOllama]:
    """Get a configured LLM instance with automatic provider detection.
    
    Tested and supported models:
    - OpenAI: gpt-4o-mini (default)
    - Ollama: gpt-oss:latest, deepseek-r1:latest, qwen3:latest
    
    Args:
        model: Model name (defaults to OPENAI_MODEL env var or gpt-4o-mini)
        temperature: Temperature for generation (default: 0, can be overridden with TEST_TEMPERATURE env var)
        max_retries: Maximum number of retries on failure (default: 2)
        timeout: Request timeout in seconds (default: 120)
        
    Returns:
        Configured LLM instance (ChatOpenAI or ChatOllama)
        
    Raises:
        ValueError: If model provider is not supported or API key is missing
        RuntimeError: If model initialization fails
    """
    if model is None:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Allow temperature override via environment variable for testing
    if temperature is None:
        temperature = float(os.getenv("TEST_TEMPERATURE", "0"))
    
    # Tested Ollama models with tool calling support
    OLLAMA_MODELS = {"gpt-oss:latest", "deepseek-r1:latest", "qwen3:latest"}
    
    # Determine provider based on model name
    is_ollama = model in OLLAMA_MODELS or "gpt-oss" in model.lower() or "deepseek" in model.lower() or "qwen" in model.lower()
    
    if is_ollama:
        try:
            return ChatOllama(
                model=model,
                temperature=temperature,
                timeout=timeout,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Ollama model '{model}'. "
                f"Please ensure Ollama is running ('ollama serve') and the model is available ('ollama pull {model}'). "
                f"Error: {str(e)}"
            ) from e
    else:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError(
                f"OPENAI_API_KEY not found in environment. "
                f"Please set your OpenAI API key to use model '{model}'."
            )
        
        try:
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=openai_api_key,
                max_tokens=None,
                timeout=timeout,
                max_retries=max_retries,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize OpenAI model '{model}'. "
                f"Please verify your API key and model name. "
                f"Error: {str(e)}"
            ) from e
            
            
    
