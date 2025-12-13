import os
from typing import Literal
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph import END

from .state import AgentState, ClarificationDecision, SupervisorDecision
from .configuration import Configuration
from .tools import search_businesses, get_business_details, analyze_reviews_sentiment
from .prompts import clarification_system_prompt, supervisor_prompt
from shared.prompts import summary_generation_prompt
from shared.config import get_llm
from shared.tool_execution import execute_tool_with_tracking
from shared.summary_utils import generate_summary
from shared.chat_utils import handle_general_chat
from shared.supervisor_utils import make_supervisor_decision, get_node_mapping

# Initialize the language model
# Uses TEST_MODEL environment variable if set (for testing), otherwise defaults to gpt-4o-mini
# For example, to use an Ollama model, call get_llm("deepseek-r1:latest")
# Ensure you have pulled and are running the appropriate model if using Ollama
# For more details, see shared/config.py
llm = get_llm(os.getenv("TEST_MODEL", "gpt-oss:20b"))

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
    Uses shared supervisor logic from supervisor_utils.
    """
    # Use shared supervisor decision logic (V2 mode: no error checking)
    next_action, error_message, update_dict = make_supervisor_decision(
        state=state,
        llm=llm,
        supervisor_decision_model=SupervisorDecision,
        prompt_generator=supervisor_prompt,
        check_failures=False,      # V2: No error tracking
        use_dual_messages=False    # V2: Single system message
    )
    
    # Handle error cases
    if error_message:
        update = {"messages": [AIMessage(content=error_message)]}
        if update_dict:
            update.update(update_dict)
        return Command(goto="summary", update=update)
    
    # Map decision to next node
    mapping = get_node_mapping()
    return Command(goto=mapping[next_action])

def general_chat_node(state: AgentState):
    """Handles non-Yelp/business queries using the chat completion endpoint."""
    # Use shared chat handling logic
    reply, _ = handle_general_chat(state, track_errors=False)
    
    return Command(
        goto=END,
        update={"messages": [AIMessage(content=reply)]}
    )

def summary_node(state: AgentState):
    """Generates the final report using the detailed v1-style prompt."""
    # Use shared summary generation logic
    final_summary = generate_summary(
        state=state,
        llm=llm,
        summary_prompt_func=summary_generation_prompt,
        include_user_question=False,
        use_dual_messages=False
    )
    
    return Command(
        goto=END,
        update={"messages": [AIMessage(content=final_summary)], "final_summary": final_summary}
    )


def search_tool_node(state: AgentState):
    query = f"{state['search_query']} in {state['search_location']}"
    
    # Use shared tool execution logic
    update = execute_tool_with_tracking(
        tool_func=search_businesses,
        tool_name="search",
        tool_args={"query": query},
        state=state,
        track_errors=False,
        add_metadata=False
    )
    
    return Command(goto="supervisor", update=update)

def details_tool_node(state: AgentState):
    # Use the actual pipeline data from search results
    pipeline1_output = state.get('pipeline_data', {})
    
    # Use shared tool execution logic
    update = execute_tool_with_tracking(
        tool_func=get_business_details,
        tool_name="details",
        tool_args={"pipeline1_output": pipeline1_output},
        state=state,
        track_errors=False,
        add_metadata=False
    )
    
    return Command(goto="supervisor", update=update)

def sentiment_tool_node(state: AgentState):
    # Use the actual pipeline data from search results
    pipeline1_output = state.get('pipeline_data', {})
    
    # Use shared tool execution logic
    update = execute_tool_with_tracking(
        tool_func=analyze_reviews_sentiment,
        tool_name="sentiment",
        tool_args={"pipeline1_output": pipeline1_output},
        state=state,
        track_errors=False,
        add_metadata=False
    )
    
    return Command(goto="supervisor", update=update)

