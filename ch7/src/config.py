"""Configuration management for the Hybrid RAG application."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Optional API Keys
    tavily_api_key: Optional[str] = Field(default=None, env="TAVILY_API_KEY")
    
    # Elasticsearch Configuration  
    elasticsearch_host: str = Field(default="http://localhost:9200", env="ELASTICSEARCH_HOST")
    elasticsearch_index: str = Field(default="documents", env="ELASTICSEARCH_INDEX")
    
    # Model Configuration
    embedder_model: str = Field(default="text-embedding-3-small", env="EMBEDDER_MODEL")
    llm_model: str = Field(default="gpt-4o-mini", env="LLM_MODEL")
    ranker_model: str = Field(default="BAAI/bge-reranker-base", env="RANKER_MODEL")
    
    # Retrieval Configuration
    top_k: int = Field(default=3, env="TOP_K")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Indexing Configuration
    run_indexing_on_startup: bool = Field(default=False, env="RUN_INDEXING_ON_STARTUP")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields instead of raising an error


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the application settings."""
    return settings


def is_elasticsearch_available(host: str = None) -> bool:
    """Check if Elasticsearch is available."""
    import requests
    
    host = host or settings.elasticsearch_host
    try:
        response = requests.get(f"{host}/_cat/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def wait_for_elasticsearch(host: str = None, max_retries: int = 30, delay: int = 2) -> bool:
    """Wait for Elasticsearch to be available."""
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    host = host or settings.elasticsearch_host
    
    for attempt in range(max_retries):
        if is_elasticsearch_available(host):
            logger.info(f"Elasticsearch is available at {host}")
            return True
        
        logger.info(f"Waiting for Elasticsearch at {host}... (attempt {attempt + 1}/{max_retries})")
        time.sleep(delay)
    
    logger.error(f"Elasticsearch not available at {host} after {max_retries} attempts")
    return False