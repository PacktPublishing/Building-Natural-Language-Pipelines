from typing import Literal
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph import END

from .state import AgentState, ClarificationDecision, SupervisorDecision
from .configuration import Configuration
from .tools import search_businesses, get_business_details, analyze_reviews_sentiment, chat_completion
from .prompts import clarification_system_prompt, supervisor_prompt, summary_prompt
from shared.prompts import summary_generation_prompt
from shared.config import get_llm

# Initialize the language model
llm = get_llm("qwen3")

def clarify_intent_node(state: AgentState, config: RunnableConfig) -> Command[Literal["supervisor", "general_chat", END]]:
    """
    Analyzes conversation to determine intent. Routes to either:
    - general_chat: For non-business questions
    - supervisor: For business searches
    - END: If clarification is needed from user
    """
    conf = Configuration.from_runnable_config(config)
    
    # 1. Define the structured output model
    clarifier_model = llm.with_structured_output(ClarificationDecision)
    
    # 2. Create context from history
    messages = state["messages"]
    
    # 2b. Generate the state-aware system prompt
    #     We pass it the *current* query and location from the state.
    system_prompt_content = clarification_system_prompt(
        current_query=state.get('search_query', ''),
        current_location=state.get('search_location', '')
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
        
        # This logic (from our last fix) is now correct.
        # The problem was that `decision.detail_level` was wrong.
        # Now, it will be correct (e.g., "reviews").
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
            # This is a follow-up. Just update the detail level.
            # The clarifier, now state-aware, will correctly set
            # decision.detail_level to "reviews"
            update_dict = {
                "detail_level": decision.detail_level,
                "messages": [AIMessage(content=f"Understood. I'll get more details for {decision.search_query}...")],
            }

        return Command(
            goto="supervisor",
            update=update_dict
        )

def supervisor_node(state: AgentState) -> Command[Literal["search_tool", "details_tool", "sentiment_tool", "summary"]]:
    """
    Acts as the brain of the search process.
    Decides which tool to call based on what data we have vs. what we need.
    """
    
    supervisor_model = llm.with_structured_output(SupervisorDecision)
    
    # Check what data we *actually* have based on the structured state
    agent_outputs = state.get('agent_outputs', {})
    has_search_data = agent_outputs.get("search", {}).get("success", False)
    has_details_data = agent_outputs.get("details", {}).get("success", False)
    has_sentiment_data = agent_outputs.get("sentiment", {}).get("success", False)

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
        "finalize": "summary"
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
    # Use the detailed v1 prompt from shared/prompts.py
    # This prompt is excellent as it's already designed to use 'agent_outputs'
    prompt = summary_generation_prompt(
        clarified_query=state['search_query'],
        clarified_location=state['search_location'],
        detail_level=state['detail_level'],
        agent_outputs=state.get('agent_outputs', {}), 
        needs_revision=False,
        revision_feedback=""
    )
    
    response = llm.invoke([SystemMessage(content=prompt)])
    return Command(
        goto=END,
        update={"messages": [response], "final_summary": response.content}
    )


def search_tool_node(state: AgentState):
    query = f"{state['search_query']} in {state['search_location']}"
    result = search_businesses.invoke({"query": query})
    # Store the full output for downstream pipelines
    full_output = result.get('full_output', {}) if result.get('success') else {}
    
    # Store in state as agent_outputs dict (v1 compatible format)
    existing_outputs = state.get('agent_outputs', {})
    existing_outputs['search'] = result
    
    return Command(
        goto="supervisor", # Return to supervisor to decide next step
        update={
            "pipeline_data": full_output,
            "agent_outputs": existing_outputs
        }
    )

def details_tool_node(state: AgentState):
    # Use the actual pipeline data from search results
    pipeline1_output = state.get('pipeline_data', {})
    result = get_business_details.invoke({"pipeline1_output": pipeline1_output})
    
    # Store in state as agent_outputs dict (v1 compatible format)
    existing_outputs = state.get('agent_outputs', {})
    existing_outputs['details'] = result
    
    
    return Command(
        goto="supervisor",
        update={
            "agent_outputs": existing_outputs
        }
    )

def sentiment_tool_node(state: AgentState):
    # Use the actual pipeline data from search results
    pipeline1_output = state.get('pipeline_data', {})
    result = analyze_reviews_sentiment.invoke({"pipeline1_output": pipeline1_output})
    
    # Store in state as agent_outputs dict (v1 compatible format)
    existing_outputs = state.get('agent_outputs', {})
    existing_outputs['sentiment'] = result
    
    
    return Command(
        goto="supervisor",
        update={
            # "raw_results": raw_results, # <--- REMOVED
            "agent_outputs": existing_outputs
        }
    )