from typing import Literal
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.graph import END

from .state import AgentState, ClarificationDecision, SupervisorDecision
from .configuration import Configuration
from .tools import search_businesses, get_business_details, analyze_reviews_sentiment, chat_completion
from .prompts import clarification_system_prompt, supervisor_prompt, summary_prompt

# Initialize your model (ensure you have your LLM setup here)
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv(".env")  # Load environment variables from .env file
llm = ChatOpenAI(model="gpt-4o", temperature=0)

def clarify_intent_node(state: AgentState, config: RunnableConfig) -> Command[Literal["supervisor", "general_chat", END]]:
    """
    Analyzes conversation to determine intent. Routes to either:
    - general_chat: For non-business questions (uses chat completion endpoint)
    - supervisor: For business searches (uses the 4 Yelp pipelines)
    - END: If clarification is needed from user
    
    This implements the Deep Research Pattern by stopping to ask for missing info.
    """
    conf = Configuration.from_runnable_config(config)
    
    # 1. Define the structured output model
    clarifier_model = llm.with_structured_output(ClarificationDecision)
    
    # 2. Create context from history
    messages = state["messages"]
    
    # 3. Invoke model with system prompt from prompts.py
    decision: ClarificationDecision = clarifier_model.invoke([SystemMessage(content=clarification_system_prompt)] + messages)
    
    # 4. Handle Clarification (The "Stop" Mechanism)
    if decision.need_clarification and conf.allow_clarification:
        # This stops the graph and sends the question to the user
        return Command(
            goto=END,
            update={"messages": [AIMessage(content=decision.clarification_question)]}
        )
    
    # 5. Route to appropriate workflow
    if decision.intent == "general_chat":
        # Route to chat completion endpoint for general conversation
        return Command(goto="general_chat")
    else:
        # Route to supervisor for business search using the 4 pipelines
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
    
    # Construct context for supervisor using prompt from prompts.py
    context = supervisor_prompt(
        search_query=state['search_query'],
        search_location=state['search_location'],
        detail_level=state['detail_level'],
        raw_results=state['raw_results']
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
    """Generates the final report."""
    # Use prompt from prompts.py
    prompt = summary_prompt(
        search_query=state['search_query'],
        search_location=state['search_location'],
        raw_results=state['raw_results']
    )
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
    # Store the full output for downstream pipelines
    full_output = result.get('full_output', {}) if result.get('success') else {}
    # Also store a human-readable summary in raw_results
    return Command(
        goto="supervisor", # Return to supervisor to decide next step
        update={
            "raw_results": [f"Search Results: {str(result)}"],
            "pipeline_data": full_output
        }
    )

def details_tool_node(state: AgentState):
    # Use the actual pipeline data from search results
    pipeline1_output = state.get('pipeline_data', {})
    result = get_business_details.invoke({"pipeline1_output": pipeline1_output})
    return Command(
        goto="supervisor",
        update={"raw_results": [f"Details: {str(result)}"]}
    )

def sentiment_tool_node(state: AgentState):
    # Use the actual pipeline data from search results
    pipeline1_output = state.get('pipeline_data', {})
    result = analyze_reviews_sentiment.invoke({"pipeline1_output": pipeline1_output})
    return Command(
        goto="supervisor",
        update={"raw_results": [f"Sentiment: {str(result)}"]}
    )