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
from shared.config import get_llm
from shared.tools import search_businesses, get_business_details, analyze_reviews_sentiment, chat_completion

# Initialize the language model
llm = get_llm("qwen3")


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
    """
    supervisor_model = llm.with_structured_output(SupervisorDecision)
    
    # Check what data we have
    agent_outputs = state.get('agent_outputs', {})
    has_search_data = agent_outputs.get("search", {}).get("success", False)
    has_details_data = agent_outputs.get("details", {}).get("success", False)
    has_sentiment_data = agent_outputs.get("sentiment", {}).get("success", False)
    
    # Check for consecutive failures to prevent infinite loops
    consecutive_failures = state.get('consecutive_failures', {})
    MAX_CONSECUTIVE_FAILURES = 3
    
    # If any tool has failed too many times consecutively, finalize with what we have
    for tool_name, failure_count in consecutive_failures.items():
        if failure_count >= MAX_CONSECUTIVE_FAILURES:
            error_message = (
                f"I apologize, but I'm experiencing persistent issues with the {tool_name} service. "
                f"Let me provide you with the best information I can based on what's available."
            )
            return Command(
                goto="summary",
                update={
                    "messages": [AIMessage(content=error_message)],
                }
            )
    
    # Check for rate limiting or service unavailability
    rate_limited = False
    service_unavailable = False
    for tool_name, output in agent_outputs.items():
        if not output.get("success", True):
            if output.get("rate_limited", False):
                rate_limited = True
            error_msg = output.get("error", "").lower()
            if "unavailable" in error_msg or "connection" in error_msg or "timeout" in error_msg:
                service_unavailable = True
    
    # If rate limited or service unavailable, exit immediately
    if rate_limited or service_unavailable:
        error_type = "rate limit" if rate_limited else "service unavailability"
        error_message = (
            f"I apologize, but I'm unable to complete your request due to {error_type}. "
            f"The Yelp API service is currently unavailable or has rate limits in effect. "
            f"Please try again later."
        )
        return Command(
            goto=END,
            update={
                "messages": [AIMessage(content=error_message)],
                "final_summary": error_message
            }
        )
    
    # Build error context for supervisor awareness
    error_context = ""
    error_count = state.get("total_error_count", 0)
    if error_count > 0:
        error_details = []
        for tool_name, output in agent_outputs.items():
            if not output.get("success", True):
                error_msg = output.get("error", "Unknown error")
                retry_count = state.get("retry_counts", {}).get(tool_name, 0)
                error_details.append(f"- {tool_name}: {error_msg} (retries: {retry_count})")
        
        if error_details:
            error_context = "Errors encountered:\n" + "\n".join(error_details)
    
    # Construct context for supervisor
    context = supervisor_prompt_v3(
        search_query=state['search_query'],
        search_location=state['search_location'],
        detail_level=state['detail_level'],
        has_search_data=has_search_data,
        has_details_data=has_details_data,
        has_sentiment_data=has_sentiment_data,
        error_context=error_context
    )
    
    try:
        # Gemini requires at least one non-system message, so include a HumanMessage
        # For other models, the system message alone works fine
        messages_for_invoke = [
            SystemMessage(content=context),
            HumanMessage(content="Please analyze the current state and decide the next action.")
        ]
        decision: SupervisorDecision = supervisor_model.invoke(messages_for_invoke)
        
        # Debug: log the decision
        print(f"Supervisor decision: {decision.next_action} (should_finalize_early: {decision.should_finalize_early})")
        
        # If supervisor decides to finalize early due to errors, respect that
        if decision.should_finalize_early or decision.next_action == "finalize":
            return Command(goto="summary")
        
        # Map decision to next node
        mapping = {
            "search": "search_tool",
            "get_details": "details_tool",
            "analyze_sentiment": "sentiment_tool",
            "finalize": "summary"
        }
        
        return Command(goto=mapping[decision.next_action])
        
    except Exception as e:
        # If supervisor fails, try to finalize with what we have
        print(f"Supervisor error: {str(e)}")
        error_msg = f"I encountered an issue coordinating the search: {str(e)}"
        return Command(
            goto="summary",
            update={
                "messages": [AIMessage(content=error_msg)],
                "total_error_count": state.get("total_error_count", 0) + 1
            }
        )


def general_chat_node(state: AgentState):
    """Handles non-Yelp/business queries using the chat completion endpoint."""
    def message_to_dict(msg):
        """Convert LangChain messages to OpenAI format."""
        if hasattr(msg, "type") and hasattr(msg, "content"):
            role_mapping = {"human": "user", "ai": "assistant", "system": "system"}
            role = role_mapping.get(msg.type.lower(), "user")
            return {"role": role, "content": msg.content}
        if isinstance(msg, dict):
            return msg
        return {"role": "user", "content": str(msg)}

    try:
        # Convert conversation history to OpenAI message format
        messages = [message_to_dict(m) for m in state["messages"]]
        
        # Call the chat completion endpoint
        response = chat_completion.invoke({"messages": messages})
        
        # Extract the assistant's reply
        reply = None
        if response.get("success"):
            response_data = response.get("response", {})
            choices = response_data.get("choices", [])
            
            if choices and len(choices) > 0:
                message = choices[0].get("message", {})
                reply = message.get("content", "")
                
            if not reply:
                reply = f"I received a response but couldn't extract the content. Please try again."
        else:
            error_msg = response.get('error', 'Unknown error')
            reply = f"I encountered an error: {error_msg}. Please try again."

        return Command(
            goto=END,
            update={"messages": [AIMessage(content=reply)]}
        )
        
    except Exception as e:
        return Command(
            goto=END,
            update={
                "messages": [AIMessage(content=f"I encountered an unexpected error: {str(e)}. Please try again.")],
                "total_error_count": state.get("total_error_count", 0) + 1
            }
        )


def summary_node(state: AgentState):
    """Generates the final report using the detailed v1-style prompt."""
    try:
        # Extract the latest user question for context-aware summarization
        user_question = ""
        messages = state.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, 'type') and msg.type == "human":
                user_question = msg.content
                break
        
        # Use the detailed prompt from shared/prompts.py
        prompt = summary_generation_prompt(
            clarified_query=state['search_query'],
            clarified_location=state['search_location'],
            detail_level=state['detail_level'],
            agent_outputs=state.get('agent_outputs', {}),
            needs_revision=False,
            revision_feedback="",
            user_question=user_question
        )
        
        # Gemini requires at least one non-system message
        messages_for_summary = [
            SystemMessage(content=prompt),
            HumanMessage(content="Please generate the final summary based on the information provided.")
        ]
        response = llm.invoke(messages_for_summary)
        
        return Command(
            goto=END,
            update={
                "messages": [response],
                "final_summary": response.content,
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
    start_time = time.time()
    query = f"{state['search_query']} in {state['search_location']}"
    print(f"Search tool executing with query: '{query}'")
    
    try:
        result = search_businesses.invoke({"query": query})
        execution_time = time.time() - start_time
        
        # Enhance result with metadata
        if result.get("success"):
            result['metadata'] = {
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': datetime.now().isoformat(),
                'query_used': query,
                'retry_count': state.get("retry_counts", {}).get("search", 0)
            }
            
            # Store the full output for downstream pipelines
            full_output = result.get('full_output', {})
            existing_outputs = state.get('agent_outputs', {})
            existing_outputs['search'] = result
            
            # Reset consecutive failures on success
            consecutive_failures = state.get('consecutive_failures', {})
            consecutive_failures['search'] = 0
            
            return Command(
                goto="supervisor",
                update={
                    "pipeline_data": full_output,
                    "agent_outputs": existing_outputs,
                    "consecutive_failures": consecutive_failures,
                    "last_node_executed": "search_tool"
                }
            )
        else:
            # Tool returned an error
            result['metadata'] = {
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': datetime.now().isoformat()
            }
            existing_outputs = state.get('agent_outputs', {})
            existing_outputs['search'] = result
            
            # Increment consecutive failures
            consecutive_failures = state.get('consecutive_failures', {})
            consecutive_failures['search'] = consecutive_failures.get('search', 0) + 1
            
            return Command(
                goto="supervisor",
                update={
                    "agent_outputs": existing_outputs,
                    "total_error_count": state.get("total_error_count", 0) + 1,
                    "consecutive_failures": consecutive_failures,
                    "last_node_executed": "search_tool"
                }
            )
            
    except Exception as e:
        # Unexpected error during tool execution
        execution_time = time.time() - start_time
        print(f"Search tool error: {type(e).__name__}: {str(e)}")
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "metadata": {
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        existing_outputs = state.get('agent_outputs', {})
        existing_outputs['search'] = error_result
        retry_counts = state.get("retry_counts", {})
        retry_counts["search"] = retry_counts.get("search", 0) + 1
        
        # Increment consecutive failures
        consecutive_failures = state.get('consecutive_failures', {})
        consecutive_failures['search'] = consecutive_failures.get('search', 0) + 1
        
        return Command(
            goto="supervisor",
            update={
                "agent_outputs": existing_outputs,
                "total_error_count": state.get("total_error_count", 0) + 1,
                "retry_counts": retry_counts,
                "consecutive_failures": consecutive_failures,
                "last_node_executed": "search_tool"
            }
        )


def details_tool_node(state: AgentState):
    """
    V3 Details tool node with enhanced error handling.
    Note: Retry policy is configured at graph compilation level.
    """
    start_time = time.time()
    pipeline1_output = state.get('pipeline_data', {})
    
    try:
        result = get_business_details.invoke({"pipeline1_output": pipeline1_output})
        execution_time = time.time() - start_time
        
        # Enhance result with metadata
        if result.get("success"):
            result['metadata'] = {
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': datetime.now().isoformat(),
                'retry_count': state.get("retry_counts", {}).get("details", 0)
            }
        else:
            result['metadata'] = {
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': datetime.now().isoformat()
            }
        
        existing_outputs = state.get('agent_outputs', {})
        existing_outputs['details'] = result
        
        # Track consecutive failures
        consecutive_failures = state.get('consecutive_failures', {})
        if result.get("success"):
            consecutive_failures['details'] = 0
        else:
            consecutive_failures['details'] = consecutive_failures.get('details', 0) + 1
        
        update_dict = {
            "agent_outputs": existing_outputs,
            "consecutive_failures": consecutive_failures,
            "last_node_executed": "details_tool"
        }
        
        if not result.get("success"):
            update_dict["total_error_count"] = state.get("total_error_count", 0) + 1
        
        return Command(goto="supervisor", update=update_dict)
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "metadata": {
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        existing_outputs = state.get('agent_outputs', {})
        existing_outputs['details'] = error_result
        retry_counts = state.get("retry_counts", {})
        retry_counts["details"] = retry_counts.get("details", 0) + 1
        
        # Increment consecutive failures
        consecutive_failures = state.get('consecutive_failures', {})
        consecutive_failures['details'] = consecutive_failures.get('details', 0) + 1
        
        return Command(
            goto="supervisor",
            update={
                "agent_outputs": existing_outputs,
                "total_error_count": state.get("total_error_count", 0) + 1,
                "retry_counts": retry_counts,
                "consecutive_failures": consecutive_failures,
                "last_node_executed": "details_tool"
            }
        )


def sentiment_tool_node(state: AgentState):
    """
    V3 Sentiment tool node with enhanced error handling.
    Note: Retry policy is configured at graph compilation level.
    """
    start_time = time.time()
    pipeline1_output = state.get('pipeline_data', {})
    
    try:
        result = analyze_reviews_sentiment.invoke({"pipeline1_output": pipeline1_output})
        execution_time = time.time() - start_time
        
        # Enhance result with metadata
        if result.get("success"):
            result['metadata'] = {
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': datetime.now().isoformat(),
                'retry_count': state.get("retry_counts", {}).get("sentiment", 0)
            }
        else:
            result['metadata'] = {
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': datetime.now().isoformat()
            }
        
        existing_outputs = state.get('agent_outputs', {})
        existing_outputs['sentiment'] = result
        
        # Track consecutive failures
        consecutive_failures = state.get('consecutive_failures', {})
        if result.get("success"):
            consecutive_failures['sentiment'] = 0
        else:
            consecutive_failures['sentiment'] = consecutive_failures.get('sentiment', 0) + 1
        
        update_dict = {
            "agent_outputs": existing_outputs,
            "consecutive_failures": consecutive_failures,
            "last_node_executed": "sentiment_tool"
        }
        
        if not result.get("success"):
            update_dict["total_error_count"] = state.get("total_error_count", 0) + 1
        
        return Command(goto="supervisor", update=update_dict)
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "metadata": {
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        existing_outputs = state.get('agent_outputs', {})
        existing_outputs['sentiment'] = error_result
        retry_counts = state.get("retry_counts", {})
        retry_counts["sentiment"] = retry_counts.get("sentiment", 0) + 1
        
        # Increment consecutive failures
        consecutive_failures = state.get('consecutive_failures', {})
        consecutive_failures['sentiment'] = consecutive_failures.get('sentiment', 0) + 1
        
        return Command(
            goto="supervisor",
            update={
                "agent_outputs": existing_outputs,
                "total_error_count": state.get("total_error_count", 0) + 1,
                "retry_counts": retry_counts,
                "consecutive_failures": consecutive_failures,
                "last_node_executed": "sentiment_tool"
            }
        )
