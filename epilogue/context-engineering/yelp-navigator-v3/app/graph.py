"""V3 Graph with retry policies, checkpointing support and guardrails

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
    input_guardrails_node, clarify_intent_node, supervisor_node, general_chat_node, 
    summary_node, search_tool_node, details_tool_node, sentiment_tool_node
)


def build_graph(checkpointer=None):
    """
    Build the V3 graph with input guardrails before clarify.
    
    Flow:
    1. START → input_guardrails (check prompt injection, sanitize PII)
    2. → clarify (determine intent)
    3. → supervisor/tools OR general_chat
    4. → summary → END
    
    Guardrails are a separate node for visibility.
    
    Args:
        checkpointer: Optional checkpointer for conversation persistence.
                     If None, creates a MemorySaver for basic persistence.
                     Pass False to disable persistence entirely.
    
    Returns:
        Compiled graph with retry policies and checkpointing
    """
    workflow = StateGraph(AgentState, config_schema=Configuration)

    # Add Nodes (V4 with input guardrails)
    workflow.add_node("input_guardrails", input_guardrails_node)
    workflow.add_node("clarify", clarify_intent_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("general_chat", general_chat_node)
    workflow.add_node("summary", summary_node)
    
    # Tool Nodes with Retry Policies
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

    # Edges (V4 flow with input guardrails)
    workflow.add_edge(START, "input_guardrails")
    # input_guardrails → clarify (via Command)
    # clarify → supervisor/general_chat (via Command)
    # supervisor → tools (via Command)
    # tools → supervisor (via Command)
    # supervisor → summary (via Command)
    # summary/general_chat → END (via Command)

    # Compile with checkpointing
    if checkpointer is False:
        return workflow.compile()
    elif checkpointer is None:
        checkpointer = MemorySaver()
    
    return workflow.compile(checkpointer=checkpointer)


# Default export for LangGraph Studio/API
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
    
    # Use SQLite persistence for production:
    from langgraph.checkpoint.sqlite import SqliteSaver
    checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
    graph = get_graph_with_persistence(checkpointer)
    """
    return build_graph(checkpointer)

