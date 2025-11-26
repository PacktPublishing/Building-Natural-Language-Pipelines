"""V3 Nodes with enhanced error handling and retry support."""
import time
from typing import Literal, Union
from datetime import datetime
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph import END

from .state import AgentState, ClarificationDecision, SupervisorDecision
from .configuration import Configuration
from .prompts import clarification_system_prompt_v3, supervisor_prompt_v3, summary_generation_prompt
from .guardrails import apply_guardrails
from shared.config import get_llm
from shared.tools import search_businesses, get_business_details, analyze_reviews_sentiment
from shared.tool_execution import execute_tool_with_tracking
from shared.summary_utils import generate_summary
from shared.chat_utils import handle_general_chat
from shared.supervisor_utils import make_supervisor_decision, get_node_mapping

# Initialize the language model (it defaults to gpt-4o-mini, pass model name)
# For example, to use an Ollama model, call get_llm("deepseek-r1:latest")
# Ensure you have pulled the appropriate model running if using Ollama
# For more details, see shared/config.py
llm = get_llm("qwen3:latest")


def input_guardrails_node(state: AgentState, config: RunnableConfig) -> Command[Literal["clarify"]]:
    """
    Input guardrails node that checks for prompt injection and sanitizes PII.
    
    This node runs before clarify_intent_node to ensure input is safe.
    Applies minimal checks:
    1. Prompt injection detection - blocks suspicious patterns
    2. PII sanitization - redacts emails, phones, SSNs
    
    Args:
        state: Current agent state
        config: Configuration with guardrails settings
    
    Returns:
        Command to proceed to clarify or end with warning
    """
    conf = Configuration.from_runnable_config(config)
    
    # Apply guardrails if enabled
    if conf.enable_guardrails or conf.sanitize_pii:
        updated_state, warning = apply_guardrails(
            state, 
            enable_guardrails=conf.enable_guardrails,
            sanitize_pii_flag=conf.sanitize_pii
        )
        
        # If warning detected (e.g., prompt injection), block and return warning
        if warning:
            return Command(
                goto=END,
                update={"messages": [AIMessage(content=warning)]}
            )
        
        # If state was updated (e.g., PII sanitized), use updated state
        if updated_state != state:
            return Command(
                goto="clarify",
                update={"messages": updated_state["messages"]}
            )
    
    # No issues detected, proceed to clarify
    return Command(goto="clarify")


def clarify_intent_node(state: AgentState, config: RunnableConfig) -> Command[Literal["supervisor", "general_chat"]]:
    """
    V3 Clarification node with enhanced error handling.
    Analyzes conversation to determine intent and routes appropriately.
    """
    conf = Configuration.from_runnable_config(config)
    
    try:
        # Define the structured output model
        clarifier_model = llm.with_structured_output(ClarificationDecision)
        
        # Create context from history
        messages = state["messages"]
        
        # Generate the state-aware system prompt
        system_prompt_content = clarification_system_prompt_v3(
            current_query=state.get('search_query', ''),
            current_location=state.get('search_location', '')
        )
        
        # Invoke model with the dynamic system prompt
        decision: ClarificationDecision = clarifier_model.invoke(
            [SystemMessage(content=system_prompt_content)] + messages
        )
        
        # Handle Clarification
        if decision.need_clarification and conf.allow_clarification:
            return Command(
                goto=END,
                update={"messages": [AIMessage(content=decision.clarification_question)]}
            )
        
        # Route to appropriate workflow
        if decision.intent == "general_chat":
            return Command(goto="general_chat")
        else:
            # Check if this is a new search query
            is_new_search = (
                decision.search_query != state.get("search_query") or
                decision.search_location != state.get("search_location")
            )
            
            if is_new_search:
                # Brand new search - reset everything
                update_dict = {
                    "search_query": decision.search_query,
                    "search_location": decision.search_location,
                    "detail_level": decision.detail_level,
                    "messages": [AIMessage(content=f"Understood. Starting a new search for {decision.search_query} in {decision.search_location}...")],
                    "pipeline_data": {},
                    "agent_outputs": {},
                    "execution_start_time": datetime.now().isoformat(),
                    "total_error_count": 0,
                    "retry_counts": {}
                }
            else:
                # Follow-up query - determine if we need new data or can use cached data
                existing_detail = state.get("detail_level", "general")
                has_search_data = state.get('agent_outputs', {}).get("search", {}).get("success", False)
                
                # If staying at "general" detail level and we already have search data, we're just analyzing
                if decision.detail_level == "general" and existing_detail == "general" and has_search_data:
                    response_msg = "Let me analyze the results for you..."
                elif decision.detail_level != existing_detail:
                    response_msg = f"Understood. I'll get more details for {decision.search_query}..."
                else:
                    response_msg = "Let me check that for you..."
                
                update_dict = {
                    "detail_level": decision.detail_level,
                    "messages": [AIMessage(content=response_msg)],
                }

            return Command(goto="supervisor", update=update_dict)
            
    except Exception as e:
        # Handle errors in clarification gracefully
        error_msg = f"I encountered an issue understanding your request: {str(e)}. Could you please rephrase?"
        return Command(
            goto=END,
            update={
                "messages": [AIMessage(content=error_msg)],
                "total_error_count": state.get("total_error_count", 0) + 1
            }
        )

def supervisor_node(state: AgentState) -> Command[Literal["search_tool", "details_tool", "sentiment_tool", "summary"]]:
    """
    V3 Supervisor with enhanced error awareness.
    Decides which tool to call based on state and error context.
    Uses shared supervisor logic from supervisor_utils with V3 features enabled.
    """
    # Use shared supervisor decision logic (V3 mode: with error checking)
    next_action, error_message, update_dict = make_supervisor_decision(
        state=state,
        llm=llm,
        supervisor_decision_model=SupervisorDecision,
        prompt_generator=supervisor_prompt_v3,
        check_failures=True,       # V3: Enable error tracking and circuit breaker
        use_dual_messages=True,    # V3: Use both system and human messages (Gemini compatible)
        max_consecutive_failures=3
    )
    
    # Handle error cases
    if error_message:
        # Build update dict with error info
        update = {"messages": [AIMessage(content=error_message)]}
        
        # Check if this is a critical error that should exit immediately (not just go to summary)
        if "rate limit" in error_message.lower() or "unavailable" in error_message.lower():
            update["final_summary"] = error_message
            if update_dict:
                update.update(update_dict)
            return Command(goto=END, update=update)
        
        # Otherwise, go to summary with what we have
        if update_dict:
            update.update(update_dict)
        return Command(goto="summary", update=update)
    
    # Map decision to next node
    mapping = get_node_mapping()
    return Command(goto=mapping[next_action])


def general_chat_node(state: AgentState):
    """Handles non-Yelp/business queries using the chat completion endpoint."""
    # Use shared chat handling logic with error tracking enabled
    reply, error_info = handle_general_chat(state, track_errors=True)
    
    # Build update dict
    update_dict = {"messages": [AIMessage(content=reply)]}
    
    # Track errors if any occurred
    if error_info and "error_count" in error_info:
        update_dict["total_error_count"] = state.get("total_error_count", 0) + error_info["error_count"]
    
    return Command(goto=END, update=update_dict)


def summary_node(state: AgentState):
    """Generates the final report using the detailed v1-style prompt."""
    try:
        # Use shared summary generation logic with V3 features enabled
        final_summary = generate_summary(
            state=state,
            llm=llm,
            summary_prompt_func=summary_generation_prompt,
            include_user_question=True,   # V3 feature: extract user question
            use_dual_messages=True         # V3 feature: use both system and human messages
        )
        
        return Command(
            goto=END,
            update={
                "messages": [AIMessage(content=final_summary)],
                "final_summary": final_summary,
                "last_node_executed": "summary"
            }
        )
        
    except Exception as e:
        # Fallback summary if LLM fails
        fallback_msg = f"I gathered some information but encountered an error generating the summary: {str(e)}"
        return Command(
            goto=END,
            update={
                "messages": [AIMessage(content=fallback_msg)],
                "final_summary": fallback_msg,
                "total_error_count": state.get("total_error_count", 0) + 1
            }
        )


def search_tool_node(state: AgentState):
    """
    V3 Search tool node with enhanced error handling and metadata tracking.
    Note: Retry policy is configured at graph compilation level.
    """
    query = f"{state['search_query']} in {state['search_location']}"
    print(f"Search tool executing with query: '{query}'")
    
    # Use shared tool execution logic with V3 features enabled
    update = execute_tool_with_tracking(
        tool_func=search_businesses,
        tool_name="search",
        tool_args={"query": query},
        state=state,
        track_errors=True,
        add_metadata=True
    )
    
    return Command(goto="supervisor", update=update)


def details_tool_node(state: AgentState):
    """
    V3 Details tool node with enhanced error handling.
    Note: Retry policy is configured at graph compilation level.
    """
    pipeline1_output = state.get('pipeline_data', {})
    
    # Use shared tool execution logic with V3 features enabled
    update = execute_tool_with_tracking(
        tool_func=get_business_details,
        tool_name="details",
        tool_args={"pipeline1_output": pipeline1_output},
        state=state,
        track_errors=True,
        add_metadata=True
    )
    
    return Command(goto="supervisor", update=update)


def sentiment_tool_node(state: AgentState):
    """
    V3 Sentiment tool node with enhanced error handling.
    Note: Retry policy is configured at graph compilation level.
    """
    pipeline1_output = state.get('pipeline_data', {})
    
    # Use shared tool execution logic with V3 features enabled
    update = execute_tool_with_tracking(
        tool_func=analyze_reviews_sentiment,
        tool_name="sentiment",
        tool_args={"pipeline1_output": pipeline1_output},
        state=state,
        track_errors=True,
        add_metadata=True
    )
    
    return Command(goto="supervisor", update=update)
