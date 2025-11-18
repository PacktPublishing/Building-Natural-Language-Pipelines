"""Application package bootstrap and public API for Yelp Navigator V3.

Responsibilities:
- Load environment variables from a local .env at import time for local development.
- Provide organized modules for graphs, models, state, tools, memory, and utilities.
- Expose key submodules via __all__ for convenient imports.

V3 Features:
- Memory-aware business caching using SQLite
- Follow-up question support using cached data
- Reduced API calls for repeated queries
"""
from __future__ import annotations

# Load environment variables from a .env file at import time so local servers pick them up
try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(), override=False)
except Exception:
    # dotenv not installed or .env not found; continue silently
    pass

# Import key components for easy access
from .app import graph, nodes, state, tools, memory

__version__ = "3.0.0"

__all__ = [
    "tools",
    "graph",
    "nodes",
    "state",
    "memory",
]
