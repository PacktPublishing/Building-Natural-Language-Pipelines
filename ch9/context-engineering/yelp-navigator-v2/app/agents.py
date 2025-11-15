
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from .state import AgentState
from .tools import search_businesses, get_business_details, analyze_reviews_sentiment, chat_completion
from .prompts import clarification_prompt, supervisor_approval_prompt, summary_generation_prompt
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv(".env")

# Initialize the language model (should be configured with API key)
# Create a local model with Ollama

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# Chat completion agent node for general queries
def chat_completion_agent_node(state: AgentState) -> AgentState:
    """Agent node that handles general queries using the Hayhooks chat completion endpoint."""
    user_query = state.get("user_query", "")
    messages = state.get("messages", [])
    # Prepare messages for chat completion endpoint
    chat_messages = []
    if user_query:
        chat_messages.append({"role": "user", "content": user_query})
    # Optionally add previous context
    for m in messages:
        if hasattr(m, "content") and hasattr(m, "type"):
            chat_messages.append({"role": m.type.lower(), "content": m.content})
    # Call the chat completion tool
    result = chat_completion.invoke({"messages": chat_messages})
    agent_outputs = state.get("agent_outputs", {})
    agent_outputs["chat_completion"] = result
    # Prepare response
    if result.get("success"):
        output = result.get("output", {})
        choices = output.get("choices", [])
        if choices:
            reply = choices[0].get("message", {}).get("content", "")
        else:
            reply = str(output)
        summary = f"💬 Chat Completion Response:\n{reply}"
    else:
        summary = f"❌ Chat completion failed: {result.get('error', 'Unknown error')}"
    return {
        "messages": [AIMessage(content=summary)],
        "agent_outputs": agent_outputs,
        "next_agent": "end"
    }


def clarification_agent(state: AgentState) -> AgentState:
    """Agent that clarifies user intent before delegating to specialized agents."""
    
    # Check if this is the first interaction
    user_query = state.get("user_query", "")
    
    # Count how many clarification attempts have been made
    messages = state.get("messages", [])
    clarification_attempts = sum(1 for m in messages if isinstance(m, AIMessage) and "CLARIFIED:" not in m.content)
    
    # If we've tried too many times, make best guess with defaults
    if clarification_attempts >= 2:
        # Force completion with reasonable defaults
        return {
            "messages": [AIMessage(content="⚠️ Using default values: searching for restaurants in United States with general detail level.")],
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


def search_agent_node(state: AgentState) -> AgentState:
    """Search agent that finds businesses."""
    
    clarified_query = state.get("clarified_query", "")
    clarified_location = state.get("clarified_location", "")
    full_query = f"{clarified_query} in {clarified_location}"
    
    # Call the search tool
    result = search_businesses.invoke({"query": full_query})
    
    # Store the result
    agent_outputs = state.get("agent_outputs", {})
    agent_outputs["search"] = result
    
    # Create summary message
    if result.get("success"):
        businesses = result.get("businesses", [])
        summary = f"""🔍 Search Agent Results:
Found {result.get('result_count', 0)} businesses total
Top {len(businesses)} results retrieved:
"""
        for i, biz in enumerate(businesses[:5], 1):
            summary += f"\n{i}. {biz['name']} - {biz['rating']}⭐ ({biz['review_count']} reviews) - {biz.get('price_range', 'N/A')}"
    else:
        summary = f"❌ Search failed: {result.get('error', 'Unknown error')}"
    
    # Determine next agent based on detail level
    detail_level = state.get("detail_level", "general")
    
    if detail_level == "general":
        next_agent = "summary"
    elif detail_level == "detailed":
        next_agent = "details"
    else:  # reviews
        next_agent = "details"
    
    return {
        "messages": [AIMessage(content=summary)],
        "agent_outputs": agent_outputs,
        "next_agent": next_agent
    }


def details_agent_node(state: AgentState) -> AgentState:
    """Details agent that fetches website information."""
    
    agent_outputs = state.get("agent_outputs", {})
    search_output = agent_outputs.get("search", {})
    
    if not search_output.get("success"):
        return {
            "messages": [AIMessage(content="⚠️ Skipping details - no search results available")],
            "next_agent": "summary"
        }
    
    # Get pipeline1 output from search results
    pipeline1_output = search_output.get("full_output", {})
    
    # Call the details tool with keyword argument
    result = get_business_details.invoke({"pipeline1_output": pipeline1_output})
    
    agent_outputs["details"] = result
    
    # Create summary message
    if result.get("success"):
        details = result.get("businesses_with_details", [])
        summary = f"""🌐 Details Agent Results:
Retrieved detailed information for {result.get('document_count', 0)} businesses:
"""
        for i, biz in enumerate(details[:3], 1):
            website_status = "✅ Has website content" if biz['has_website_info'] else "❌ No website info"
            summary += f"\n{i}. {biz['name']} - {website_status}"
    else:
        summary = f"❌ Details fetch failed: {result.get('error', 'Unknown error')}"
    
    # Determine next agent
    detail_level = state.get("detail_level", "general")
    next_agent = "sentiment" if detail_level == "reviews" else "summary"
    
    return {
        "messages": [AIMessage(content=summary)],
        "agent_outputs": agent_outputs,
        "next_agent": next_agent
    }


def sentiment_agent_node(state: AgentState) -> AgentState:
    """Sentiment agent that analyzes reviews."""
    
    agent_outputs = state.get("agent_outputs", {})
    search_output = agent_outputs.get("search", {})
    
    if not search_output.get("success"):
        return {
            "messages": [AIMessage(content="⚠️ Skipping sentiment analysis - no search results available")],
            "next_agent": "summary"
        }
    
    # Get pipeline1 output from search results
    pipeline1_output = search_output.get("full_output", {})
    
    # Call the sentiment tool with keyword argument
    result = analyze_reviews_sentiment.invoke({"pipeline1_output": pipeline1_output})
    
    agent_outputs["sentiment"] = result
    
    # Create summary message
    if result.get("success"):
        sentiments = result.get("sentiment_summaries", [])
        summary = f"""💬 Sentiment Agent Results:
Analyzed reviews for {result.get('analyzed_count', 0)} businesses:
"""
        for i, biz in enumerate(sentiments[:3], 1):
            total = biz['positive_count'] + biz['neutral_count'] + biz['negative_count']
            if total > 0:
                positive_pct = (biz['positive_count'] / total) * 100
                summary += f"\n{i}. {biz['name']}"
                summary += f"\n   Sentiment: {biz['positive_count']}😊 {biz['neutral_count']}😐 {biz['negative_count']}😞 ({positive_pct:.0f}% positive)"
    else:
        summary = f"❌ Sentiment analysis failed: {result.get('error', 'Unknown error')}"
    
    return {
        "messages": [AIMessage(content=summary)],
        "agent_outputs": agent_outputs,
        "next_agent": "summary"
    }

def supervisor_approval_agent(state: AgentState) -> AgentState:
    """Supervisor reviews the summary and decides if it's complete or needs revision."""
    
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
            "messages": [AIMessage(content="✅ Supervisor: Approval limit reached. Accepting current summary.")],
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
            "messages": [AIMessage(content="✅ Supervisor: Summary approved! All requirements met.")],
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
    
    supervisor_message = f"""⚠️ Supervisor: Summary needs revision.
Feedback: {feedback}
Action: Re-running {rerun_agent} agent..."""
    
    return {
        "messages": [AIMessage(content=supervisor_message)],
        "next_agent": rerun_agent,
        "needs_revision": True,
        "revision_feedback": feedback,
        "approval_attempts": approval_attempts + 1
    }

def summary_agent_node(state: AgentState) -> AgentState:
    """Summary agent that creates the final human-readable response."""
    
    agent_outputs = state.get("agent_outputs", {})
    clarified_query = state.get("clarified_query", "")
    clarified_location = state.get("clarified_location", "")
    detail_level = state.get("detail_level", "general")
    needs_revision = state.get("needs_revision", False)
    revision_feedback = state.get("revision_feedback", "")
    
    # Get summary generation prompt from prompts module
    context = summary_generation_prompt(
        clarified_query=clarified_query,
        clarified_location=clarified_location,
        detail_level=detail_level,
        agent_outputs=agent_outputs,
        needs_revision=needs_revision,
        revision_feedback=revision_feedback
    )
    
    # Generate summary using LLM
    response = llm.invoke([SystemMessage(content=context)])
    final_summary = response.content
    
    return {
        "messages": [AIMessage(content=f"\n\n📝 SUMMARY DRAFT:\n\n{final_summary}")],
        "final_summary": final_summary,
        "next_agent": "supervisor_approval",
        "needs_revision": False  # Reset flag after generating new summary
    }
