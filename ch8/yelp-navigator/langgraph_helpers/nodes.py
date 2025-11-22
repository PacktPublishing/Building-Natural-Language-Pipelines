"""Node implementations for LangGraph multi-agent system."""

from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage

def search_agent_node(state: Dict[str, Any], search_businesses: tool) -> Dict[str, Any]:
    """Search agent that finds businesses."""
    full_query = f"{state.get('clarified_query', '')} in {state.get('clarified_location', '')}"
    result = search_businesses.invoke({"query": full_query})
    
    agent_outputs = state.get("agent_outputs", {})
    agent_outputs["search"] = result
    
    if result.get("success"):
        businesses = result.get("businesses", [])
        summary = f"Found {result.get('result_count', 0)} businesses:\n"
        summary += "\n".join(f"{i}. {b['name']} - {b['rating']} stars ({b['review_count']} reviews)" 
                             for i, b in enumerate(businesses, 1))
    else:
        summary = f"Search failed: {result.get('error', 'Unknown error')}"
    
    detail_level = state.get("detail_level", "general")
    next_agent = "summary" if detail_level == "general" else "details"
    
    return {"messages": [AIMessage(content=summary)], "agent_outputs": agent_outputs, "next_agent": next_agent}


def details_agent_node(state: Dict[str, Any], get_business_details: tool) -> Dict[str, Any]:
    """Details agent that fetches website information."""
    agent_outputs = state.get("agent_outputs", {})
    search_output = agent_outputs.get("search", {})
    
    if not search_output.get("success"):
        return {"messages": [AIMessage(content="Skipping details")], "next_agent": "summary"}
    
    result = get_business_details.invoke({"pipeline1_output": search_output.get("full_output", {})})
    agent_outputs["details"] = result
    
    if result.get("success"):
        details = result.get("businesses_with_details", [])
        summary = f"Retrieved details for {result.get('document_count', 0)} businesses:\n"
        summary += "\n".join(f"{i}. {b['name']} - {'Has website' if b['has_website_info'] else 'No website'}" 
                             for i, b in enumerate(details, 1))
    else:
        summary = f"Details failed: {result.get('error', 'Unknown error')}"
    
    next_agent = "sentiment" if state.get("detail_level") == "reviews" else "summary"
    return {"messages": [AIMessage(content=summary)], "agent_outputs": agent_outputs, "next_agent": next_agent}


def sentiment_agent_node(state: Dict[str, Any], analyze_reviews_sentiment: tool) -> Dict[str, Any]:
    """Sentiment agent that analyzes reviews."""
    agent_outputs = state.get("agent_outputs", {})
    search_output = agent_outputs.get("search", {})
    
    if not search_output.get("success"):
        return {"messages": [AIMessage(content="Skipping sentiment")], "next_agent": "summary"}
    
    result = analyze_reviews_sentiment.invoke({"pipeline1_output": search_output.get("full_output", {})})
    agent_outputs["sentiment"] = result
    
    if result.get("success"):
        sentiments = result.get("sentiment_summaries", [])
        id_to_name = {b.get('id'): b.get('name', 'Unknown') for b in search_output.get("businesses", [])}
        
        summary = f"Analyzed {result.get('business_count', 0)} businesses:\n"
        for i, biz in enumerate(sentiments, 1):
            name = id_to_name.get(biz.get('business_id'), f"Business {biz.get('business_id')}")
            total = biz['positive_count'] + biz['neutral_count'] + biz['negative_count']
            pos_pct = (biz['positive_count'] / total * 100) if total > 0 else 0
            summary += f"\n{i}. {name}: +{biz['positive_count']} ={biz['neutral_count']} -{biz['negative_count']} ({pos_pct:.0f}% positive)"
    else:
        summary = f"Sentiment failed: {result.get('error', 'Unknown error')}"
    
    return {"messages": [AIMessage(content=summary)], "agent_outputs": agent_outputs, "next_agent": "summary"}


def summary_agent_node(state: Dict[str, Any], llm) -> Dict[str, Any]:
    """Summary agent that creates the final human-readable response."""
    
    agent_outputs = state.get("agent_outputs", {})
    
    context = f"""Create a friendly summary for: {state.get('clarified_query')} in {state.get('clarified_location')} (detail: {state.get('detail_level')})
"""
    if state.get("needs_revision") and state.get("revision_feedback"):
        context += f"\nADDRESS THIS FEEDBACK: {state['revision_feedback']}\n"
    
    # Add search results
    if "search" in agent_outputs and agent_outputs["search"].get("success"):
        search = agent_outputs["search"]
        context += f"\n\nFOUND {search['result_count']} BUSINESSES:\n"
        for i, biz in enumerate(search.get("businesses", []), 1):
            context += f"{i}. {biz['name']} - {biz['rating']} stars ({biz['review_count']} reviews) - {biz.get('price_range', 'N/A')}\n"
    
    # Add details if available
    if "details" in agent_outputs and agent_outputs["details"].get("success"):
        context += "\n\nWEBSITE INFO:\n"
        for i, biz in enumerate(agent_outputs["details"].get("businesses_with_details", []), 1):
            status = "Has website" if biz['has_website_info'] else "No website"
            context += f"{i}. {biz['name']} - {status}\n"
    
    # Add sentiment if available
    if "sentiment" in agent_outputs and agent_outputs["sentiment"].get("success"):
        search = agent_outputs.get("search", {})
        id_to_name = {b.get('id'): b.get('name', 'Unknown') for b in search.get("businesses", [])}
        context += "\n\nREVIEW SENTIMENT:\n"
        for i, biz in enumerate(agent_outputs["sentiment"].get("sentiment_summaries", []), 1):
            name = id_to_name.get(biz.get('business_id'), f"Business {biz.get('business_id')}")
            context += f"{i}. {name} - +{biz['positive_count']} ={biz['neutral_count']} -{biz['negative_count']}\n"
            if biz.get('highest_rated_reviews'):
                context += f"   Best: {biz['highest_rated_reviews'][0].get('text', '')[:100]}...\n"
    
    context += "\n\nWrite a friendly, conversational summary with top recommendations."
    
    response = llm.invoke([SystemMessage(content=context)])
    return {
        "messages": [AIMessage(content=f"SUMMARY:\n\n{response.content}")],
        "final_summary": response.content, "next_agent": "supervisor_approval", "needs_revision": False
    }
