from langgraph.graph import StateGraph, START
from .state import AgentState
from .configuration import Configuration
from .nodes import (
    clarify_intent_node, supervisor_node, general_chat_node, 
    summary_node, search_tool_node, details_tool_node, sentiment_tool_node
)

def build_graph():
    workflow = StateGraph(AgentState, config_schema=Configuration)

    # Add Nodes
    workflow.add_node("clarify", clarify_intent_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("general_chat", general_chat_node)
    workflow.add_node("summary", summary_node)
    
    # Tool Nodes
    workflow.add_node("search_tool", search_tool_node)
    workflow.add_node("details_tool", details_tool_node)
    workflow.add_node("sentiment_tool", sentiment_tool_node)

    # Edges
    # Start at clarification. The node logic handles the rest via Command(goto=...)
    workflow.add_edge(START, "clarify")

    return workflow

# Compile the graph with increased recursion limit for approval loops
graph = build_graph().compile()

