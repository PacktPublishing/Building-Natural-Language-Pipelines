"""Agent definitions for LangGraph multi-agent system."""

from typing import Dict, Any
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, BaseMessage
from langchain_openai import ChatOpenAI


def clarification_agent(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    """Agent that clarifies user intent before delegating to specialized agents."""
    messages = state.get("messages", [])
    clarification_attempts = sum(1 for m in messages if isinstance(m, AIMessage) and "CLARIFIED:" not in m.content)
    
    # Force defaults after 2 attempts
    if clarification_attempts >= 2:
        return {
            "messages": [AIMessage(content="Using defaults: restaurants in United States, general detail level.")],
            "clarified_query": "restaurants", "clarified_location": "United States",
            "detail_level": "general", "clarification_complete": True, "next_agent": "search"
        }
    
    system_prompt = """Extract query, location, and detail level from user request.
                        Detail levels: "general" (basic info), "detailed" (websites), "reviews" (sentiment).
                        Use defaults if unclear: restaurants, United States, general.

                        Respond in this format when ready:
                        CLARIFIED:
                        QUERY: [search term]
                        LOCATION: [location]
                        DETAIL_LEVEL: [general/detailed/reviews]"""
    
    msg_list = [SystemMessage(content=system_prompt)] + messages
    if state.get("user_query") and not any(isinstance(m, HumanMessage) for m in messages):
        msg_list.append(HumanMessage(content=state["user_query"]))
    
    response = llm.invoke(msg_list)
    
    if "CLARIFIED:" in response.content:
        info = {}
        for line in response.content.split('\n'):
            if line.startswith("QUERY:"): info['query'] = line.replace("QUERY:", "").strip()
            elif line.startswith("LOCATION:"): info['location'] = line.replace("LOCATION:", "").strip()
            elif line.startswith("DETAIL_LEVEL:"): info['detail_level'] = line.replace("DETAIL_LEVEL:", "").strip().lower()
        
        return {
            "messages": [response],
            "clarified_query": info.get('query', 'restaurants'),
            "clarified_location": info.get('location', 'United States'),
            "detail_level": info.get('detail_level', 'general'),
            "clarification_complete": True, "next_agent": "search"
        }
    
    return {"messages": [response], "clarification_complete": False, "next_agent": "clarification"}


def supervisor_approval_agent(state: Dict[str, Any], llm: ChatOpenAI) -> Dict[str, Any]:
    """Supervisor reviews the summary and decides if it's complete or needs revision."""
    approval_attempts = state.get("approval_attempts", 0)
    
    if approval_attempts >= 2:
        return {"messages": [AIMessage(content="Supervisor: Approval limit reached.")], 
                "next_agent": "end", "approval_attempts": approval_attempts + 1}
    
    evaluation_prompt = f"""Review this summary for completeness and quality.
                        User request: {state.get('clarified_query')} in {state.get('clarified_location')} (detail: {state.get('detail_level')})

                        SUMMARY:
                        {state.get('final_summary', '')}

                        Respond with either:
                        APPROVED

                        Or:
                        NEEDS_REVISION
                        FEEDBACK: [what to improve]
                        RERUN_AGENT: [search/details/sentiment/summary]"""
    
    evaluation = llm.invoke([SystemMessage(content=evaluation_prompt)])
    
    if "APPROVED" in evaluation.content and "NEEDS_REVISION" not in evaluation.content:
        return {"messages": [AIMessage(content="Summary approved!")], "next_agent": "end", "approval_attempts": approval_attempts + 1}
    
    # Parse revision request
    feedback, rerun_agent = "", "summary"
    for line in evaluation.content.split('\n'):
        if line.startswith("FEEDBACK:"): feedback = line.replace("FEEDBACK:", "").strip()
        elif line.startswith("RERUN_AGENT:"): 
            agent = line.replace("RERUN_AGENT:", "").strip().lower()
            if agent in ["search", "details", "sentiment", "summary"]: rerun_agent = agent
    
    return {
        "messages": [AIMessage(content=f"Needs revision: {feedback}. Re-running {rerun_agent}...")],
        "next_agent": rerun_agent, "needs_revision": True, "revision_feedback": feedback or "Improve quality",
        "approval_attempts": approval_attempts + 1
    }
