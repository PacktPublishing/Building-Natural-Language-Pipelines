from langgraph.graph import StateGraph, START, END
from .agents import (
    clarification_agent, search_agent_node, details_agent_node,
    sentiment_agent_node, summary_agent_node, supervisor_approval_agent
)
from .agent_state import AgentState


def route_after_clarification(state: AgentState) -> str:
    """Route to search if clarification is complete, otherwise continue clarifying."""
    if state.get("clarification_complete", False):
        return "search"
    return "clarification"


def route_from_agents(state: AgentState) -> str:
    """Route to the next agent based on state."""
    next_agent = state.get("next_agent", "end")
    
    if next_agent == "end":
        return END
    
    return next_agent


def route_from_supervisor_approval(state: AgentState) -> str:
    """Route from supervisor approval to either END or back to an agent."""
    next_agent = state.get("next_agent", "end")
    
    if next_agent == "end":
        return END
    
    # Supervisor wants to rerun an agent
    return next_agent

def build_workflow_graph() -> StateGraph[AgentState]:
    """Builds the multi-agent workflow graph for Yelp Navigator with supervisor approval."""
    # Build the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("clarification", clarification_agent)
    workflow.add_node("search", search_agent_node)
    workflow.add_node("details", details_agent_node)
    workflow.add_node("sentiment", sentiment_agent_node)
    workflow.add_node("summary", summary_agent_node)
    workflow.add_node("supervisor_approval", supervisor_approval_agent)

    # Add edges
    workflow.add_edge(START, "clarification")

    # Conditional routing from clarification - goes directly to search when complete
    workflow.add_conditional_edges(
        "clarification",
        route_after_clarification,
        {"clarification": "clarification", "search": "search"}
    )

    # Conditional routing from specialized agents
    workflow.add_conditional_edges(
        "search",
        route_from_agents,
        {"details": "details", "sentiment": "sentiment", "summary": "summary", END: END}
    )

    workflow.add_conditional_edges(
        "details",
        route_from_agents,
        {"sentiment": "sentiment", "summary": "summary", END: END}
    )

    workflow.add_conditional_edges(
        "sentiment",
        route_from_agents,
        {"summary": "summary", END: END}
    )

    # Summary now routes to supervisor approval instead of END
    workflow.add_conditional_edges(
        "summary",
        route_from_agents,
        {"supervisor_approval": "supervisor_approval", END: END}
    )

    # Supervisor approval can route back to agents or to END
    workflow.add_conditional_edges(
        "supervisor_approval",
        route_from_supervisor_approval,
        {
            "search": "search",
            "details": "details", 
            "sentiment": "sentiment",
            "summary": "summary",
            END: END
        }
    )
    return workflow

# Compile the graph with increased recursion limit for approval loops
graph = build_workflow_graph().compile()

