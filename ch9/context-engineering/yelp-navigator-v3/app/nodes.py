from typing import Literal
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph import END

from .state import AgentState, ClarificationDecision, SupervisorDecision
from .configuration import Configuration
from .tools import (
    search_businesses_with_memory,
    get_business_details_with_memory,
    analyze_reviews_sentiment_with_memory,
    get_cached_business_info,
    list_cached_businesses,
    chat_completion,
    memory
)
from .prompts import clarification_system_prompt, supervisor_prompt, summary_prompt
from shared.prompts import summary_generation_prompt
from shared.config import get_llm

# Initialize the language model
llm = get_llm()

def clarify_intent_node(state: AgentState, config: RunnableConfig):
    """
    Analyzes conversation to determine intent. Routes to either:
    - general_chat: For non-business questions
    - check_memory: If asking about a previously mentioned business
    - supervisor: For business searches
    - END: If clarification is needed from user
    """
    conf = Configuration.from_runnable_config(config)
    
    # 1. Define the structured output model
    clarifier_model = llm.with_structured_output(ClarificationDecision)
    
    # 2. Create context from history
    messages = state["messages"]
    latest_message = messages[-1].content if messages else ""
    
    # 2a. Check if user is asking about a known business
    # Look for business names or IDs in the latest message
    known_businesses = state.get("known_business_ids", [])
    
    # Get list of cached business names to help with matching
    cached_list = []
    if known_businesses:
        for bid in known_businesses:
            cached = memory.get_business(bid)
            if cached:
                cached_list.append({"id": bid, "name": cached["name"]})
    
    # 2b. Generate the state-aware system prompt
    #     We pass it the *current* query and location from the state.
    system_prompt_content = clarification_system_prompt(
        current_query=state.get('search_query', ''),
        current_location=state.get('search_location', ''),
        known_businesses=cached_list
    )
    
    # 3. Invoke model with the NEW dynamic system prompt
    decision: ClarificationDecision = clarifier_model.invoke(
        [SystemMessage(content=system_prompt_content)] + messages
    )
    
    # 4. Handle Clarification (Unchanged)
    if decision.need_clarification and conf.allow_clarification:
        return Command(
            goto=END,
            update={"messages": [AIMessage(content=decision.clarification_question)]}
        )
    
    # 5. Route to appropriate workflow
    if decision.intent == "general_chat":
        return Command(goto="general_chat")
    else:
        # Check if this is a *new* search query
        is_new_search = (
            decision.search_query != state.get("search_query") or
            decision.search_location != state.get("search_location")
        )
        
        if is_new_search:
            # This is a brand new search. Reset everything.
            update_dict = {
                "search_query": decision.search_query,
                "search_location": decision.search_location,
                "detail_level": decision.detail_level,
                "messages": [AIMessage(content=f"Understood. Starting a new search for {decision.search_query} in {decision.search_location}...")],
                "pipeline_data": {},
                "agent_outputs": {}
            }
        else:
            # This is a follow-up. Check if we can answer from memory first
            # If we have cached businesses and detail level changed, go to check_memory
            if known_businesses and decision.detail_level != state.get("detail_level"):
                update_dict = {
                    "detail_level": decision.detail_level,
                    "messages": [AIMessage(content=f"Let me check what information I have about {decision.search_query}...")],
                }
                return Command(goto="check_memory", update=update_dict)
            else:
                # Standard follow-up
                update_dict = {
                    "detail_level": decision.detail_level,
                    "messages": [AIMessage(content=f"Understood. I'll get more details for {decision.search_query}...")],
                }

        return Command(
            goto="supervisor",
            update=update_dict
        )

def check_memory_node(state: AgentState):
    """
    Check if we have the requested information in memory before making API calls.
    
    This node examines cached business data and determines if we can answer
    the user's question without additional API calls.
    """
    known_businesses = state.get("known_business_ids", [])
    detail_level = state.get("detail_level", "general")
    cached_data = {}
    
    # Check what data we have for known businesses
    for bid in known_businesses:
        info = get_cached_business_info(bid)
        if info:
            cached_data[bid] = info
    
    # Determine if we have enough data
    needs_api_call = False
    
    if detail_level == "detailed":
        # Check if we have details for all businesses
        for bid in known_businesses:
            if bid not in cached_data or not cached_data[bid].get("has_details"):
                needs_api_call = True
                break
    elif detail_level == "reviews":
        # Check if we have sentiment data for all businesses
        for bid in known_businesses:
            if bid not in cached_data or not cached_data[bid].get("has_sentiment"):
                needs_api_call = True
                break
    
    # Update cached_businesses tracking
    cached_businesses = {}
    for bid, info in cached_data.items():
        cached_businesses[bid] = {
            "basic": True,
            "details": info.get("has_details", False),
            "sentiment": info.get("has_sentiment", False)
        }
    
    if needs_api_call:
        # Need to fetch more data
        return Command(
            goto="supervisor",
            update={
                "cached_businesses": cached_businesses,
                "messages": [AIMessage(content="Fetching additional information...")]
            }
        )
    else:
        # We have everything we need! Build output from cache
        agent_outputs = state.get("agent_outputs", {})
        
        # Mark that we used cache
        agent_outputs["from_cache"] = True
        agent_outputs["cached_data"] = cached_data
        
        return Command(
            goto="summary",
            update={
                "cached_businesses": cached_businesses,
                "agent_outputs": agent_outputs,
                "messages": [AIMessage(content="Using cached information...")]
            }
        )

def supervisor_node(state: AgentState):
    """
    Acts as the brain of the search process.
    Decides which tool to call based on what data we have vs. what we need.
    
    Now memory-aware: checks cached_businesses before deciding.
    """
    
    supervisor_model = llm.with_structured_output(SupervisorDecision)
    
    # Check what data we *actually* have based on the structured state
    agent_outputs = state.get('agent_outputs', {})
    has_search_data = agent_outputs.get("search", {}).get("success", False)
    has_details_data = agent_outputs.get("details", {}).get("success", False)
    has_sentiment_data = agent_outputs.get("sentiment", {}).get("success", False)
    
    # Check cached data availability
    cached_businesses = state.get("cached_businesses", {})
    known_business_ids = state.get("known_business_ids", [])
    
    # If we have cached businesses, check if we can use them
    if known_business_ids and cached_businesses:
        detail_level = state.get("detail_level", "general")
        
        # Check if cache has what we need
        if detail_level == "detailed":
            has_details_data = all(
                cached_businesses.get(bid, {}).get("details", False)
                for bid in known_business_ids
            )
        elif detail_level == "reviews":
            has_sentiment_data = all(
                cached_businesses.get(bid, {}).get("sentiment", False)
                for bid in known_business_ids
            )

    # Construct context for supervisor using the *new* prompt
    context = supervisor_prompt(
        search_query=state['search_query'],
        search_location=state['search_location'],
        detail_level=state['detail_level'],
        has_search_data=has_search_data,
        has_details_data=has_details_data,
        has_sentiment_data=has_sentiment_data
    )
    
    decision: SupervisorDecision = supervisor_model.invoke([SystemMessage(content=context)])
    
    # Map decision to next node
    mapping = {
        "search": "search_tool",
        "get_details": "details_tool",
        "analyze_sentiment": "sentiment_tool",
        "finalize": "summary",
        "check_memory": "check_memory"
    }
    
    return Command(goto=mapping[decision.next_action])

def general_chat_node(state: AgentState):
    """Handles non-Yelp/business queries using the chat completion endpoint."""
    def message_to_dict(msg):
        """Convert LangChain messages to OpenAI format."""
        if hasattr(msg, "type") and hasattr(msg, "content"):
            # Map LangChain message types to OpenAI roles
            role_mapping = {
                "human": "user",
                "ai": "assistant",
                "system": "system"
            }
            role = role_mapping.get(msg.type.lower(), "user")
            return {"role": role, "content": msg.content}
        if isinstance(msg, dict):
            return msg
        return {"role": "user", "content": str(msg)}

    # Convert conversation history to OpenAI message format
    messages = [message_to_dict(m) for m in state["messages"]]
    
    # Call the chat completion endpoint
    response = chat_completion.invoke({"messages": messages})
    
    # Extract the assistant's reply from the OpenAI-compatible response
    reply = None
    if response.get("success"):
        response_data = response.get("response", {})
        choices = response_data.get("choices", [])
        
        if choices and len(choices) > 0:
            # Extract content from the first choice's message
            message = choices[0].get("message", {})
            reply = message.get("content", "")
            
        if not reply:
            # Fallback if structure is unexpected
            reply = f"WARNING: Received response but couldn't extract content: {response_data}"
    else:
        # Handle error case
        error_msg = response.get('error', 'Unknown error')
        reply = f"ERROR: Chat completion failed: {error_msg}"

    return Command(
        goto=END,
        update={"messages": [AIMessage(content=reply)]}
    )

def summary_node(state: AgentState):
    """Generates the final report using the detailed v1-style prompt."""
    # Check if we used cached data
    agent_outputs = state.get('agent_outputs', {})
    used_cache = agent_outputs.get("from_cache", False)
    
    # Use the detailed v1 prompt from shared/prompts.py
    prompt = summary_generation_prompt(
        clarified_query=state['search_query'],
        clarified_location=state['search_location'],
        detail_level=state['detail_level'],
        agent_outputs=agent_outputs,
        needs_revision=False,
        revision_feedback=""
    )
    
    # Add note about using cached data if applicable
    if used_cache:
        prompt += "\n\nNOTE: Some or all of this information was retrieved from cached data based on previous queries."
    
    response = llm.invoke([SystemMessage(content=prompt)])
    return Command(
        goto=END,
        update={"messages": [response], "final_summary": response.content}
    )


def search_tool_node(state: AgentState):
    """Search for businesses and cache results."""
    query = f"{state['search_query']} in {state['search_location']}"
    result = search_businesses_with_memory(query)
    
    # Store the full output for downstream pipelines
    full_output = result.get('full_output', {}) if result.get('success') else {}
    
    # Track known business IDs
    business_ids = result.get("cached_business_ids", [])
    
    # Store in state as agent_outputs dict (v1 compatible format)
    existing_outputs = state.get('agent_outputs', {})
    existing_outputs['search'] = result
    
    # Update cached_businesses tracking
    cached_businesses = state.get("cached_businesses", {})
    for bid in business_ids:
        if bid not in cached_businesses:
            cached_businesses[bid] = {"basic": True, "details": False, "sentiment": False}
    
    return Command(
        goto="supervisor",
        update={
            "pipeline_data": full_output,
            "agent_outputs": existing_outputs,
            "known_business_ids": business_ids,
            "cached_businesses": cached_businesses
        }
    )

def details_tool_node(state: AgentState):
    """Get business details, checking cache first."""
    # Use the actual pipeline data from search results
    pipeline1_output = state.get('pipeline_data', {})
    known_business_ids = state.get("known_business_ids", [])
    
    # Call memory-aware version
    result = get_business_details_with_memory(
        pipeline1_output=pipeline1_output,
        business_ids=known_business_ids if known_business_ids else None
    )
    
    # Store in state as agent_outputs dict (v1 compatible format)
    existing_outputs = state.get('agent_outputs', {})
    existing_outputs['details'] = result
    
    # Update cached_businesses tracking
    if result.get("success"):
        cached_businesses = state.get("cached_businesses", {})
        for bid in known_business_ids:
            if bid in cached_businesses:
                cached_businesses[bid]["details"] = True
    
    return Command(
        goto="supervisor",
        update={
            "agent_outputs": existing_outputs,
            "cached_businesses": cached_businesses
        }
    )

def sentiment_tool_node(state: AgentState):
    """Analyze sentiment, checking cache first."""
    # Use the actual pipeline data from search results
    pipeline1_output = state.get('pipeline_data', {})
    known_business_ids = state.get("known_business_ids", [])
    
    # Call memory-aware version
    result = analyze_reviews_sentiment_with_memory(
        pipeline1_output=pipeline1_output,
        business_ids=known_business_ids if known_business_ids else None
    )
    
    # Store in state as agent_outputs dict (v1 compatible format)
    existing_outputs = state.get('agent_outputs', {})
    existing_outputs['sentiment'] = result
    
    # Update cached_businesses tracking
    if result.get("success"):
        cached_businesses = state.get("cached_businesses", {})
        for bid in known_business_ids:
            if bid in cached_businesses:
                cached_businesses[bid]["sentiment"] = True
    
    return Command(
        goto="supervisor",
        update={
            "agent_outputs": existing_outputs,
            "cached_businesses": cached_businesses
        }
    )
