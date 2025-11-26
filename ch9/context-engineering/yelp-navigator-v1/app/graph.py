from langgraph.graph import StateGraph, START, END
from .nodes import (
    clarification_node, search_node, details_node,
    sentiment_node, summary_node, supervisor_approval_node
)
from .state import AgentState


def route_after_clarification(state: AgentState) -> str:
    """Route to search if clarification is complete, otherwise continue clarifying."""
    if state.get("clarification_complete", False):
        return "search"
    return "clarification"


def route_after_search(state: AgentState) -> str:
    """Route based on detail level: general->summary, detailed/reviews->details."""
    detail_level = state.get("detail_level", "general")
    
    if detail_level == "general":
        return "summary"
    else:  # detailed or reviews - both need details first
        return "details"


def route_after_details(state: AgentState) -> str:
    """Route from details node based on detail level."""
    detail_level = state.get("detail_level", "general")
    
    if detail_level == "reviews":
        return "sentiment"
    else:
        return "summary"


def route_from_supervisor_approval(state: AgentState) -> str:
    """Route from supervisor approval to either END or back to an agent."""
    next_agent = state.get("next_agent", "end")
    
    if next_agent == "end":
        return END
    
    # Supervisor wants to rerun an agent
    return next_agent

def build_workflow_graph() -> StateGraph[AgentState]:
    """Builds a true pipeline architecture for Yelp Navigator.
    
    Pipeline Flow:
    1. Clarify → Search (sequential, clarify may loop)
    2. Search → Sentiment OR Details OR Summary (based on detail_level)
    3. Details → Sentiment OR Summary (based on detail_level)
    4. Sentiment → Summary (always)
    5. Summary → Approval (always)
    6. Approval → END or back to any step for revision
    """
    # Build the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("clarification", clarification_node)
    workflow.add_node("search", search_node)
    workflow.add_node("details", details_node)
    workflow.add_node("sentiment", sentiment_node)
    workflow.add_node("summary", summary_node)
    workflow.add_node("supervisor_approval", supervisor_approval_node)

    # Add edges - TRUE PIPELINE ARCHITECTURE
    # START -> Clarification (may loop back to itself)
    workflow.add_edge(START, "clarification")

    # Clarification loops or moves to search
    workflow.add_conditional_edges(
        "clarification",
        route_after_clarification,
        {"clarification": "clarification", "search": "search"}
    )

    # Search -> Details OR Summary (based on detail level)
    workflow.add_conditional_edges(
        "search",
        route_after_search,
        {"details": "details", "summary": "summary"}
    )

    # Details -> Sentiment OR Summary (based on detail level)
    workflow.add_conditional_edges(
        "details",
        route_after_details,
        {"sentiment": "sentiment", "summary": "summary"}
    )

    # Sentiment -> Summary (always)
    workflow.add_edge("sentiment", "summary")

    # Summary -> Supervisor Approval (always)
    workflow.add_edge("summary", "supervisor_approval")

    # Supervisor Approval can route back to agents or to END
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

