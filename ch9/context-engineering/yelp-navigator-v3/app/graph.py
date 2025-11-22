"""V3 Graph with retry policies and checkpointing support.

Note: The default `graph` export does NOT include a checkpointer, making it compatible
with LangGraph Studio/API which provides persistence automatically. 

For standalone usage with custom persistence, use `get_graph_with_persistence()`.
"""
from langgraph.graph import StateGraph, START
from langgraph.types import RetryPolicy
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .configuration import Configuration
from .nodes import (
    clarify_intent_node, supervisor_node, general_chat_node, 
    summary_node, search_tool_node, details_tool_node, sentiment_tool_node
)


def build_graph(checkpointer=None):
    """
    Build the V3 graph with enhanced error handling and optional persistence.
    
    Args:
        checkpointer: Optional checkpointer for conversation persistence.
                     If None, creates a MemorySaver for basic persistence.
                     Pass False to disable persistence entirely.
    
    Returns:
        Compiled graph with retry policies and checkpointing
    """
    workflow = StateGraph(AgentState, config_schema=Configuration)

    # Add Nodes
    workflow.add_node("clarify", clarify_intent_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("general_chat", general_chat_node)
    workflow.add_node("summary", summary_node)
    
    # Tool Nodes with Retry Policies (High Priority Feature #1)
    # These retry policies handle transient failures like network issues
    retry_policy = RetryPolicy(
        max_attempts=3,
        initial_interval=1.0,
        backoff_factor=2.0,
        max_interval=10.0
    )
    
    workflow.add_node(
        "search_tool", 
        search_tool_node,
        retry_policy=retry_policy
    )
    workflow.add_node(
        "details_tool", 
        details_tool_node,
        retry_policy=retry_policy
    )
    workflow.add_node(
        "sentiment_tool", 
        sentiment_tool_node,
        retry_policy=retry_policy
    )

    # Edges
    # Start at clarification. The node logic handles the rest via Command(goto=...)
    workflow.add_edge(START, "clarify")

    # Compile with checkpointing (High Priority Feature #2)
    if checkpointer is False:
        # Explicitly disable checkpointing
        return workflow.compile()
    elif checkpointer is None:
        # Default: use MemorySaver for basic in-memory persistence
        checkpointer = MemorySaver()
    
    return workflow.compile(checkpointer=checkpointer)


# Default export for LangGraph Studio/API
# NO checkpointer - the platform provides persistence automatically
graph = build_graph(checkpointer=False)


def get_graph_with_persistence(checkpointer=None):
    """
    Get a graph instance with custom checkpointer for standalone usage.
    
    ⚠️ Note: When using LangGraph Studio/API, use the default `graph` export instead.
    The platform provides persistence automatically and custom checkpointers will be ignored.
    
    This function is for standalone Python usage outside of LangGraph Studio/API.
    
    Usage examples:
    
    # Use in-memory persistence for development:
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    graph = get_graph_with_persistence(checkpointer)
    
    # Use PostgreSQL for production:
    from langgraph.checkpoint.postgres import PostgresSaver
    checkpointer = PostgresSaver(connection_string="postgresql://...")
    graph = get_graph_with_persistence(checkpointer)
    
    # Disable persistence for testing:
    graph = get_graph_with_persistence(checkpointer=False)
    """
    return build_graph(checkpointer)
