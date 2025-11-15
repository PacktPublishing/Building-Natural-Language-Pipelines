from typing import Literal
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph import END

from .state import AgentState, ClarificationDecision, SupervisorDecision
from .configuration import Configuration
from .tools import search_businesses, get_business_details, analyze_reviews_sentiment, chat_completion

# Initialize your model (ensure you have your LLM setup here)
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o", temperature=0)

def clarify_intent_node(state: AgentState, config: RunnableConfig) -> Command[Literal["supervisor", "general_chat", END]]:
    """
    Analyzes conversation to determine intent. 
    Stops and asks user if information is missing (Deep Research Pattern).
    """
    conf = Configuration.from_runnable_config(config)
    
    # 1. Define the structured output model
    clarifier_model = llm.with_structured_output(ClarificationDecision)
    
    # 2. Create context from history
    messages = state["messages"]
    system_prompt = """You are a helpful assistant. Analyze the conversation. 
    If the user wants to find a business/food, extract the query and location.
    If the location is missing, you MUST ask for clarification unless implied.
    If it's a general conversation, mark intent as 'general_chat'."""
    
    # 3. Invoke model
    decision: ClarificationDecision = clarifier_model.invoke([SystemMessage(content=system_prompt)] + messages)
    
    # 4. Handle Clarification (The "Stop" Mechanism)
    if decision.need_clarification and conf.allow_clarification:
        # This stops the graph and sends the question to the user
        return Command(
            goto=END,
            update={"messages": [AIMessage(content=decision.clarification_question)]}
        )
    
    # 5. Route to appropriate workflow
    if decision.intent == "general_chat":
        return Command(goto="general_chat")
    else:
        # Proceed to Search Supervisor with extracted context
        return Command(
            goto="supervisor",
            update={
                "search_query": decision.search_query,
                "search_location": decision.search_location,
                "detail_level": decision.detail_level,
                # Optional: Add a confirmation message
                "messages": [AIMessage(content=f"Understood. Searching for {decision.search_query} in {decision.search_location}...")]
            }
        )

def supervisor_node(state: AgentState) -> Command[Literal["search_tool", "details_tool", "sentiment_tool", "summary"]]:
    """
    Acts as the brain of the search process.
    Decides which tool to call based on what data we have vs. what we need.
    """
    
    supervisor_model = llm.with_structured_output(SupervisorDecision)
    
    # Construct context for supervisor
    context = f"""
    Goal: Find '{state['search_query']}' in '{state['search_location']}'.
    Target Detail Level: {state['detail_level']}
    
    Current Results Log:
    {state['raw_results']}
    
    Instructions:
    1. If no results yet, call 'search'.
    2. If we have results but need website info (and level is detailed/reviews), call 'get_details'.
    3. If we have results but need opinions (and level is reviews), call 'analyze_sentiment'.
    4. If we have sufficient info for the detail level, call 'finalize'.
    """
    
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
    """Handles non-Yelp queries."""
    response = chat_completion.invoke({"messages": state["messages"]})
    return Command(
        goto=END,
        update={"messages": [AIMessage(content=response.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "Error"))]}
    )

def summary_node(state: AgentState):
    """Generates the final report."""
    prompt = f"""
    Generate a friendly summary for the user about {state['search_query']} in {state['search_location']}.
    Use the following raw data:
    {state['raw_results']}
    """
    response = llm.invoke([SystemMessage(content=prompt)])
    return Command(
        goto=END,
        update={"messages": [response], "final_summary": response.content}
    )

# --- Wrapper Nodes for Tools (Adapters) ---
# These adapt your existing tools to the graph state

def search_tool_node(state: AgentState):
    query = f"{state['search_query']} in {state['search_location']}"
    result = search_businesses.invoke({"query": query})
    # We store the raw JSON/Dict as a string in 'raw_results' for the Supervisor/Summary to read
    return Command(
        goto="supervisor", # Return to supervisor to decide next step
        update={"raw_results": [f"Search Results: {str(result)}"]}
    )

def details_tool_node(state: AgentState):
    # Extract pipeline data from raw_results (simplified logic)
    # In production, you might store the actual dict in a separate state field
    result = get_business_details.invoke({"pipeline1_output": {}}) # Mock input, connect real data
    return Command(
        goto="supervisor",
        update={"raw_results": [f"Details: {str(result)}"]}
    )

def sentiment_tool_node(state: AgentState):
    result = analyze_reviews_sentiment.invoke({"pipeline1_output": {}}) # Mock input
    return Command(
        goto="supervisor",
        update={"raw_results": [f"Sentiment: {str(result)}"]}
    )