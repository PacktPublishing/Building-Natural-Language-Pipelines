import os
from typing import Dict, Any
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from .state import AgentState
from shared.tools import search_businesses, get_business_details, analyze_reviews_sentiment
from shared.prompts import clarification_prompt, supervisor_approval_prompt, summary_generation_prompt
from shared.config import get_llm
from shared.tool_execution import execute_tool_with_tracking
from shared.summary_utils import generate_summary

# Initialize the language model
# Uses TEST_MODEL environment variable if set (for testing), otherwise defaults to gpt-4o-mini
# For example, to use an Ollama model, call get_llm("deepseek-r1:latest")
# Ensure you have the appropriate model running if using Ollama
# For more details, see shared/config.py
llm = get_llm(os.getenv("TEST_MODEL"))


def clarification_node(state: AgentState) -> AgentState:
    """Node that clarifies user intent before delegating to specialized agents."""
    
    # Check if this is the first interaction
    user_query = state.get("user_query", "")
    
    # Count how many clarification attempts have been made
    messages = state.get("messages", [])
    clarification_attempts = sum(1 for m in messages if isinstance(m, AIMessage) and "CLARIFIED:" not in m.content)
    
    # If we've tried too many times, make best guess with defaults
    if clarification_attempts >= 2:
        # Force completion with reasonable defaults
        return {
            "messages": [AIMessage(content="WARNING: Using default values: searching for restaurants in United States with general detail level.")],
            "clarified_query": "restaurants",
            "clarified_location": "United States",
            "detail_level": "general",
            "clarification_complete": True,
            "next_agent": "search"
        }
    
    # Use the imported clarification_prompt
    msg_list = [SystemMessage(content=clarification_prompt)]
    msg_list.extend(messages)
    
    # If this is the first turn, add the user query
    if user_query and not any(isinstance(m, HumanMessage) for m in messages):
        msg_list.append(HumanMessage(content=user_query))
    
    # Get LLM response
    response = llm.invoke(msg_list)
    
    # Check if clarification is complete
    response_text = response.content
    
    if "CLARIFIED:" in response_text:
        # Parse the clarified information
        lines = response_text.split('\n')
        clarified_info = {}
        
        for line in lines:
            if line.startswith("QUERY:"):
                clarified_info['query'] = line.replace("QUERY:", "").strip()
            elif line.startswith("LOCATION:"):
                clarified_info['location'] = line.replace("LOCATION:", "").strip()
            elif line.startswith("DETAIL_LEVEL:"):
                clarified_info['detail_level'] = line.replace("DETAIL_LEVEL:", "").strip().lower()
        
        return {
            "messages": [response],
            "clarified_query": clarified_info.get('query', 'restaurants'),
            "clarified_location": clarified_info.get('location', 'United States'),
            "detail_level": clarified_info.get('detail_level', 'general'),
            "clarification_complete": True,
            "next_agent": "search"
        }
    else:
        # Still clarifying
        return {
            "messages": [response],
            "clarification_complete": False,
            "next_agent": "clarification"
        }


def search_node(state: AgentState) -> AgentState:
    """Node that finds businesses using search tool. Pipeline step 2."""
    
    clarified_query = state.get("clarified_query", "")
    clarified_location = state.get("clarified_location", "")
    full_query = f"{clarified_query} in {clarified_location}"
    
    # Use shared tool execution logic
    update = execute_tool_with_tracking(
        tool_func=search_businesses,
        tool_name="search",
        tool_args={"query": full_query},
        state=state,
        track_errors=False,
        add_metadata=False
    )
    
    # Create summary message
    result = update["agent_outputs"]["search"]
    if result.get("success"):
        businesses = result.get("businesses", [])
        summary = f"""Search Agent Results:
                    Found {result.get('result_count', 0)} businesses total
                    Top {len(businesses)} results retrieved:
                    """
        for i, biz in enumerate(businesses, 1):
            summary += f"\n{i}. {biz['name']} - Rating: {biz['rating']}/5 ({biz['review_count']} reviews) - {biz.get('price_range', 'N/A')}"
    else:
        summary = f"ERROR: Search failed: {result.get('error', 'Unknown error')}"
    
    # Pipeline continues to next step based on detail_level (handled by graph routing)
    return {
        **update,
        "messages": [AIMessage(content=summary)]
    }


def details_node(state: AgentState) -> AgentState:
    """Node that fetches website information. Pipeline step 3a."""
    
    agent_outputs = state.get("agent_outputs", {})
    search_output = agent_outputs.get("search", {})
    
    if not search_output.get("success"):
        return {
            "messages": [AIMessage(content="WARNING: Skipping details - no search results available")]
        }
    
    # Get pipeline1 output from search results
    pipeline1_output = search_output.get("full_output", {})
    
    # Use shared tool execution logic
    update = execute_tool_with_tracking(
        tool_func=get_business_details,
        tool_name="details",
        tool_args={"pipeline1_output": pipeline1_output},
        state=state,
        track_errors=False,
        add_metadata=False
    )
    
    # Create summary message
    result = update["agent_outputs"]["details"]
    if result.get("success"):
        details = result.get("businesses_with_details", [])
        summary = f"""Details Agent Results:\
                    Retrieved detailed information for \
                        {result.get('document_count', 0)} businesses:"""
        
        for i, biz in enumerate(details, 1):
            website_status = "[Website content available]" if biz['has_website_info'] else "[No website info]"
            summary += f"\n{i}. {biz['name']} - {website_status}"
    else:
        summary = f"ERROR: Details fetch failed: {result.get('error', 'Unknown error')}"
    
    # Pipeline continues to next step (handled by graph routing)
    return {
        **update,
        "messages": [AIMessage(content=summary)]
    }


def sentiment_node(state: AgentState) -> AgentState:
    """Node that analyzes reviews for sentiment. Pipeline step 3b or 4."""
    
    agent_outputs = state.get("agent_outputs", {})
    search_output = agent_outputs.get("search", {})
    
    if not search_output.get("success"):
        return {
            "messages": [AIMessage(content="WARNING: Skipping sentiment analysis - no search results available")]
        }
    
    # Get pipeline1 output from search results
    pipeline1_output = search_output.get("full_output", {})
    
    # Use shared tool execution logic
    update = execute_tool_with_tracking(
        tool_func=analyze_reviews_sentiment,
        tool_name="sentiment",
        tool_args={"pipeline1_output": pipeline1_output},
        state=state,
        track_errors=False,
        add_metadata=False
    )
    
    # Create summary message
    result = update["agent_outputs"]["sentiment"]
    if result.get("success"):
        # Create a mapping from business_id to business name from search results
        business_name_map = {}
        for business in search_output.get("businesses", []):
            business_name_map[business.get("id")] = business.get("name", "Unknown Business")
        
        sentiments = result.get("sentiment_summaries", [])
        summary = f"""Sentiment Agent Results:
                    Analyzed reviews for {result.get('analyzed_count', 0)} businesses:
                    """
        for i, biz in enumerate(sentiments, 1):
            total = biz['positive_count'] + biz['neutral_count'] + biz['negative_count']
            if total > 0:
                positive_pct = (biz['positive_count'] / total) * 100
                business_name = business_name_map.get(biz.get('business_id'), f"Business ID: {biz.get('business_id')}")
                summary += f"\n{i}. {business_name}"
                summary += f"\n   Sentiment: Positive: {biz['positive_count']},\
                                    Neutral: {biz['neutral_count']}, \
                                    Negative: {biz['negative_count']} ({positive_pct:.0f}% positive)"
    else:
        summary = f"ERROR: Sentiment analysis failed: {result.get('error', 'Unknown error')}"
    
    # Pipeline always continues to summary (handled by graph routing)
    return {
        **update,
        "messages": [AIMessage(content=summary)]
    }


def supervisor_approval_node(state: AgentState) -> AgentState:
    """Node where supervisor reviews the summary and decides if it's complete or needs revision."""
    
    final_summary = state.get("final_summary", "")
    detail_level = state.get("detail_level", "general")
    agent_outputs = state.get("agent_outputs", {})
    clarified_query = state.get("clarified_query", "")
    clarified_location = state.get("clarified_location", "")
    approval_attempts = state.get("approval_attempts", 0)
    
    # Limit approval loops to prevent infinite cycles
    MAX_APPROVAL_ATTEMPTS = 2
    
    if approval_attempts >= MAX_APPROVAL_ATTEMPTS:
        return {
            "messages": [AIMessage(content="APPROVED: Supervisor: Approval limit reached. Accepting current summary.")],
            "next_agent": "end",
            "approval_attempts": approval_attempts + 1
        }
    
    # Get evaluation prompt from prompts module
    evaluation_prompt_text = supervisor_approval_prompt(
        clarified_query=clarified_query,
        clarified_location=clarified_location,
        detail_level=detail_level,
        agent_outputs=agent_outputs,
        final_summary=final_summary
    )
    
    # Get supervisor's evaluation
    evaluation = llm.invoke([SystemMessage(content=evaluation_prompt_text)])
    evaluation_text = evaluation.content
    
    if "APPROVED" in evaluation_text and "NEEDS_REVISION" not in evaluation_text:
        # Summary approved!
        return {
            "messages": [AIMessage(content="APPROVED: Supervisor: Summary approved! All requirements met.")],
            "next_agent": "end",
            "approval_attempts": approval_attempts + 1
        }
    
    # Summary needs revision
    feedback_lines = evaluation_text.split('\n')
    feedback = ""
    rerun_agent = "summary"  # Default to regenerating summary
    
    for line in feedback_lines:
        if line.startswith("FEEDBACK:"):
            feedback = line.replace("FEEDBACK:", "").strip()
        elif line.startswith("RERUN_AGENT:"):
            agent_name = line.replace("RERUN_AGENT:", "").strip().lower()
            if agent_name in ["search", "details", "sentiment", "summary"]:
                rerun_agent = agent_name
    
    if not feedback:
        feedback = "Please improve the summary to better address the user's requirements."
    
    supervisor_message = f"""NEEDS_REVISION: Supervisor: Summary needs revision.
                            Feedback: {feedback}
                            Action: Re-running {rerun_agent} agent..."""
                                
    return {
        "messages": [AIMessage(content=supervisor_message)],
        "next_agent": rerun_agent,
        "needs_revision": True,
        "revision_feedback": feedback,
        "approval_attempts": approval_attempts + 1
    }


def summary_node(state: AgentState) -> AgentState:
    """Node that creates the final human-readable response. Pipeline step 4 or 5."""
    
    # Use shared summary generation logic
    final_summary = generate_summary(
        state=state,
        llm=llm,
        summary_prompt_func=summary_generation_prompt,
        include_user_question=False,
        use_dual_messages=False
    )
    
    # Pipeline always continues to supervisor approval.
    # Note: This node no longer needs to set 'next_agent' because the workflow graph
    # (see graph.py) now routes directly from 'summary' to 'supervisor_approval'.
    return {
        "messages": [AIMessage(content=f"\n\nSUMMARY DRAFT:\n\n{final_summary}")],
        "final_summary": final_summary,
        "needs_revision": False  # Reset flag after generating new summary
    }
from typing import Dict, Any
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from .state import AgentState
from shared.tools import search_businesses, get_business_details, analyze_reviews_sentiment
from shared.prompts import clarification_prompt, supervisor_approval_prompt, summary_generation_prompt
from shared.config import get_llm
from shared.tool_execution import execute_tool_with_tracking
from shared.summary_utils import generate_summary

# Initialize the language model (it defaults to gpt-4o-mini, pass model name)
# For example, to use an Ollama model, call get_llm("deepseek-r1:latest")
# Ensure you have the appropriate model running if using Ollama
# For more details, see shared/config.py
# Initialize the language model
llm = get_llm("gpt-oss:20b")  #change to your preferred model


def clarification_node(state: AgentState) -> AgentState:
    """Node that clarifies user intent before delegating to specialized agents."""
    
    # Check if this is the first interaction
    user_query = state.get("user_query", "")
    
    # Count how many clarification attempts have been made
    messages = state.get("messages", [])
    clarification_attempts = sum(1 for m in messages if isinstance(m, AIMessage) and "CLARIFIED:" not in m.content)
    
    # If we've tried too many times, make best guess with defaults
    if clarification_attempts >= 2:
        # Force completion with reasonable defaults
        return {
            "messages": [AIMessage(content="WARNING: Using default values: searching for restaurants in United States with general detail level.")],
            "clarified_query": "restaurants",
            "clarified_location": "United States",
            "detail_level": "general",
            "clarification_complete": True,
            "next_agent": "search"
        }
    
    # Use the imported clarification_prompt
    msg_list = [SystemMessage(content=clarification_prompt)]
    msg_list.extend(messages)
    
    # If this is the first turn, add the user query
    if user_query and not any(isinstance(m, HumanMessage) for m in messages):
        msg_list.append(HumanMessage(content=user_query))
    
    # Get LLM response
    response = llm.invoke(msg_list)
    
    # Check if clarification is complete
    response_text = response.content
    
    if "CLARIFIED:" in response_text:
        # Parse the clarified information
        lines = response_text.split('\n')
        clarified_info = {}
        
        for line in lines:
            if line.startswith("QUERY:"):
                clarified_info['query'] = line.replace("QUERY:", "").strip()
            elif line.startswith("LOCATION:"):
                clarified_info['location'] = line.replace("LOCATION:", "").strip()
            elif line.startswith("DETAIL_LEVEL:"):
                clarified_info['detail_level'] = line.replace("DETAIL_LEVEL:", "").strip().lower()
        
        return {
            "messages": [response],
            "clarified_query": clarified_info.get('query', 'restaurants'),
            "clarified_location": clarified_info.get('location', 'United States'),
            "detail_level": clarified_info.get('detail_level', 'general'),
            "clarification_complete": True,
            "next_agent": "search"
        }
    else:
        # Still clarifying
        return {
            "messages": [response],
            "clarification_complete": False,
            "next_agent": "clarification"
        }


def search_node(state: AgentState) -> AgentState:
    """Node that finds businesses using search tool. Pipeline step 2."""
    
    clarified_query = state.get("clarified_query", "")
    clarified_location = state.get("clarified_location", "")
    full_query = f"{clarified_query} in {clarified_location}"
    
    # Use shared tool execution logic
    update = execute_tool_with_tracking(
        tool_func=search_businesses,
        tool_name="search",
        tool_args={"query": full_query},
        state=state,
        track_errors=False,
        add_metadata=False
    )
    
    # Create summary message
    result = update["agent_outputs"]["search"]
    if result.get("success"):
        businesses = result.get("businesses", [])
        summary = f"""Search Agent Results:
                    Found {result.get('result_count', 0)} businesses total
                    Top {len(businesses)} results retrieved:
                    """
        for i, biz in enumerate(businesses, 1):
            summary += f"\n{i}. {biz['name']} - Rating: {biz['rating']}/5 ({biz['review_count']} reviews) - {biz.get('price_range', 'N/A')}"
    else:
        summary = f"ERROR: Search failed: {result.get('error', 'Unknown error')}"
    
    # Pipeline continues to next step based on detail_level (handled by graph routing)
    return {
        **update,
        "messages": [AIMessage(content=summary)]
    }


def details_node(state: AgentState) -> AgentState:
    """Node that fetches website information. Pipeline step 3a."""
    
    agent_outputs = state.get("agent_outputs", {})
    search_output = agent_outputs.get("search", {})
    
    if not search_output.get("success"):
        return {
            "messages": [AIMessage(content="WARNING: Skipping details - no search results available")]
        }
    
    # Get pipeline1 output from search results
    pipeline1_output = search_output.get("full_output", {})
    
    # Use shared tool execution logic
    update = execute_tool_with_tracking(
        tool_func=get_business_details,
        tool_name="details",
        tool_args={"pipeline1_output": pipeline1_output},
        state=state,
        track_errors=False,
        add_metadata=False
    )
    
    # Create summary message
    result = update["agent_outputs"]["details"]
    if result.get("success"):
        details = result.get("businesses_with_details", [])
        summary = f"""Details Agent Results:\
                    Retrieved detailed information for \
                        {result.get('document_count', 0)} businesses:"""
        
        for i, biz in enumerate(details, 1):
            website_status = "[Website content available]" if biz['has_website_info'] else "[No website info]"
            summary += f"\n{i}. {biz['name']} - {website_status}"
    else:
        summary = f"ERROR: Details fetch failed: {result.get('error', 'Unknown error')}"
    
    # Pipeline continues to next step (handled by graph routing)
    return {
        **update,
        "messages": [AIMessage(content=summary)]
    }


def sentiment_node(state: AgentState) -> AgentState:
    """Node that analyzes reviews for sentiment. Pipeline step 3b or 4."""
    
    agent_outputs = state.get("agent_outputs", {})
    search_output = agent_outputs.get("search", {})
    
    if not search_output.get("success"):
        return {
            "messages": [AIMessage(content="WARNING: Skipping sentiment analysis - no search results available")]
        }
    
    # Get pipeline1 output from search results
    pipeline1_output = search_output.get("full_output", {})
    
    # Use shared tool execution logic
    update = execute_tool_with_tracking(
        tool_func=analyze_reviews_sentiment,
        tool_name="sentiment",
        tool_args={"pipeline1_output": pipeline1_output},
        state=state,
        track_errors=False,
        add_metadata=False
    )
    
    # Create summary message
    result = update["agent_outputs"]["sentiment"]
    if result.get("success"):
        # Create a mapping from business_id to business name from search results
        business_name_map = {}
        for business in search_output.get("businesses", []):
            business_name_map[business.get("id")] = business.get("name", "Unknown Business")
        
        sentiments = result.get("sentiment_summaries", [])
        summary = f"""Sentiment Agent Results:
                    Analyzed reviews for {result.get('analyzed_count', 0)} businesses:
                    """
        for i, biz in enumerate(sentiments, 1):
            total = biz['positive_count'] + biz['neutral_count'] + biz['negative_count']
            if total > 0:
                positive_pct = (biz['positive_count'] / total) * 100
                business_name = business_name_map.get(biz.get('business_id'), f"Business ID: {biz.get('business_id')}")
                summary += f"\n{i}. {business_name}"
                summary += f"\n   Sentiment: Positive: {biz['positive_count']},\
                                    Neutral: {biz['neutral_count']}, \
                                    Negative: {biz['negative_count']} ({positive_pct:.0f}% positive)"
    else:
        summary = f"ERROR: Sentiment analysis failed: {result.get('error', 'Unknown error')}"
    
    # Pipeline always continues to summary (handled by graph routing)
    return {
        **update,
        "messages": [AIMessage(content=summary)]
    }


def supervisor_approval_node(state: AgentState) -> AgentState:
    """Node where supervisor reviews the summary and decides if it's complete or needs revision."""
    
    final_summary = state.get("final_summary", "")
    detail_level = state.get("detail_level", "general")
    agent_outputs = state.get("agent_outputs", {})
    clarified_query = state.get("clarified_query", "")
    clarified_location = state.get("clarified_location", "")
    approval_attempts = state.get("approval_attempts", 0)
    
    # Limit approval loops to prevent infinite cycles
    MAX_APPROVAL_ATTEMPTS = 2
    
    if approval_attempts >= MAX_APPROVAL_ATTEMPTS:
        return {
            "messages": [AIMessage(content="APPROVED: Supervisor: Approval limit reached. Accepting current summary.")],
            "next_agent": "end",
            "approval_attempts": approval_attempts + 1
        }
    
    # Get evaluation prompt from prompts module
    evaluation_prompt_text = supervisor_approval_prompt(
        clarified_query=clarified_query,
        clarified_location=clarified_location,
        detail_level=detail_level,
        agent_outputs=agent_outputs,
        final_summary=final_summary
    )
    
    # Get supervisor's evaluation
    evaluation = llm.invoke([SystemMessage(content=evaluation_prompt_text)])
    evaluation_text = evaluation.content
    
    if "APPROVED" in evaluation_text and "NEEDS_REVISION" not in evaluation_text:
        # Summary approved!
        return {
            "messages": [AIMessage(content="APPROVED: Supervisor: Summary approved! All requirements met.")],
            "next_agent": "end",
            "approval_attempts": approval_attempts + 1
        }
    
    # Summary needs revision
    feedback_lines = evaluation_text.split('\n')
    feedback = ""
    rerun_agent = "summary"  # Default to regenerating summary
    
    for line in feedback_lines:
        if line.startswith("FEEDBACK:"):
            feedback = line.replace("FEEDBACK:", "").strip()
        elif line.startswith("RERUN_AGENT:"):
            agent_name = line.replace("RERUN_AGENT:", "").strip().lower()
            if agent_name in ["search", "details", "sentiment", "summary"]:
                rerun_agent = agent_name
    
    if not feedback:
        feedback = "Please improve the summary to better address the user's requirements."
    
    supervisor_message = f"""NEEDS_REVISION: Supervisor: Summary needs revision.
                            Feedback: {feedback}
                            Action: Re-running {rerun_agent} agent..."""
                                
    return {
        "messages": [AIMessage(content=supervisor_message)],
        "next_agent": rerun_agent,
        "needs_revision": True,
        "revision_feedback": feedback,
        "approval_attempts": approval_attempts + 1
    }


def summary_node(state: AgentState) -> AgentState:
    """Node that creates the final human-readable response. Pipeline step 4 or 5."""
    
    # Use shared summary generation logic
    final_summary = generate_summary(
        state=state,
        llm=llm,
        summary_prompt_func=summary_generation_prompt,
        include_user_question=False,
        use_dual_messages=False
    )
    
    # Pipeline always continues to supervisor approval.
    # Note: This node no longer needs to set 'next_agent' because the workflow graph
    # (see graph.py) now routes directly from 'summary' to 'supervisor_approval'.
    return {
        "messages": [AIMessage(content=f"\n\nSUMMARY DRAFT:\n\n{final_summary}")],
        "final_summary": final_summary,
        "needs_revision": False  # Reset flag after generating new summary
    }
