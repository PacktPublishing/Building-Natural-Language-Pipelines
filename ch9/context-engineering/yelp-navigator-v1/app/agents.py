from typing import Dict, Any
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from .agent_state import AgentState
from .tools import search_businesses, get_business_details, analyze_reviews_sentiment

# Initialize the language model (should be configured with API key)
# Create a local model with Ollama
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


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
    
    # System prompt for clarification
    system_prompt = """You are a helpful assistant that clarifies user requests for business searches.
    
Your goal is to extract three pieces of information:
1. QUERY: What type of business/food/service are they looking for?
2. LOCATION: Where are they searching?
3. DETAIL_LEVEL: What information do they need?
   - "general": Just basic business info (name, rating, location)
   - "detailed": Include website information and additional details
   - "reviews": Include customer reviews and sentiment analysis

Analyze the user's query and extract this information. If the query is too vague and missing critical information,
you should make reasonable assumptions and proceed rather than asking for clarification.

For example:
- If they say "restaurants" without a location, use "United States" as default
- If they don't specify detail level, use "general"
- If they mention wanting "reviews" or "what people say", use "reviews" detail level

When you have all information (or can make reasonable assumptions), respond EXACTLY in this format:
CLARIFIED:
QUERY: [what they're looking for]
LOCATION: [where]
DETAIL_LEVEL: [general/detailed/reviews]
"""
    
    msg_list = [SystemMessage(content=system_prompt)]
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
    
    # Build evaluation context
    evaluation_prompt = f"""You are a supervisor reviewing a summary for quality and completeness.

USER REQUEST:
- Query: {clarified_query} in {clarified_location}
- Detail level: {detail_level}

AVAILABLE DATA:
- Search results: {"✓ Available" if agent_outputs.get("search", {}).get("success") else "✗ Not available"}
- Website details: {"✓ Available" if agent_outputs.get("details", {}).get("success") else "✗ Not available"}
- Review sentiment: {"✓ Available" if agent_outputs.get("sentiment", {}).get("success") else "✗ Not available"}

SUMMARY TO REVIEW:
{final_summary}

EVALUATION CRITERIA:
1. CRITICAL: Does it discuss businesses/restaurants related to "{clarified_query} in {clarified_location}"?
   If the summary discusses unrelated topics (programming, variables, JavaScript, etc.), it MUST be rejected.
2. Does it directly answer the user's question?
3. Are the top recommendations clearly highlighted with business names?
4. If detail_level is "detailed", does it mention website information?
5. If detail_level is "reviews", does it discuss customer sentiment and reviews?
6. Is it well-structured and easy to read?
7. Does it have a helpful closing statement?

IMPORTANT: If the summary is about a completely different topic (not business search), respond with:
NEEDS_REVISION
FEEDBACK: The summary is completely off-topic. It must discuss business search results for {clarified_query} in {clarified_location}.
RERUN_AGENT: summary

Based on your evaluation, respond in ONE of these formats:

If the summary is complete and satisfactory:
APPROVED

If the summary needs improvement:
NEEDS_REVISION
FEEDBACK: [specific feedback on what to improve]
RERUN_AGENT: [which agent to rerun: "search", "details", "sentiment", or "summary"]
"""
    
    # Get supervisor's evaluation
    evaluation = llm.invoke([SystemMessage(content=evaluation_prompt)])
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
    
    # Build context for the LLM
    context = f"""Create a comprehensive, human-readable summary based on the following information:

User was looking for: {clarified_query} in {clarified_location}
Detail level requested: {detail_level}
"""
    
    # Add revision feedback if this is a revision
    if needs_revision and revision_feedback:
        context += f"\n⚠️ SUPERVISOR FEEDBACK (please address this):\n{revision_feedback}\n"
    
    context += "\nAgent Results:\n"
    
    # Add search results
    if "search" in agent_outputs and agent_outputs["search"].get("success"):
        search = agent_outputs["search"]
        context += f"\n\nSEARCH RESULTS ({search['result_count']} total found):\n"
        for i, biz in enumerate(search.get("businesses", [])[:5], 1):
            context += f"{i}. {biz['name']}\n"
            context += f"   Rating: {biz['rating']} stars ({biz['review_count']} reviews)\n"
            context += f"   Price: {biz.get('price_range', 'N/A')}\n"
            context += f"   Categories: {', '.join(biz.get('categories', []))}\n"
            context += f"   Phone: {biz.get('phone', 'N/A')}\n\n"
    
    # Add details if available
    if "details" in agent_outputs and agent_outputs["details"].get("success"):
        details = agent_outputs["details"]
        context += "\n\nDETAILED INFORMATION:\n"
        for i, biz in enumerate(details.get("businesses_with_details", [])[:3], 1):
            context += f"{i}. {biz['name']}\n"
            if biz['has_website_info']:
                context += f"   ✓ Website information available ({biz['website_content_length']} chars)\n"
            else:
                context += f"   ✗ No website information found\n"
    
    # Add sentiment if available
    if "sentiment" in agent_outputs and agent_outputs["sentiment"].get("success"):
        sentiment = agent_outputs["sentiment"]
        context += "\n\nREVIEW SENTIMENT ANALYSIS:\n"
        for i, biz in enumerate(sentiment.get("sentiment_summaries", [])[:3], 1):
            context += f"{i}. {biz['name']}\n"
            context += f"   Positive: {biz['positive_count']}, Neutral: {biz['neutral_count']}, Negative: {biz['negative_count']}\n"
            
            # Add sample reviews
            if biz.get('top_positive_reviews'):
                context += f"   Top Review: {biz['top_positive_reviews'][0].get('text', '')[:150]}...\n"
            if biz.get('bottom_negative_reviews'):
                context += f"   Critical Review: {biz['bottom_negative_reviews'][0].get('text', '')[:150]}...\n"
    
    context += """\n\nIMPORTANT INSTRUCTIONS:
You MUST create a summary about the business search results provided above.
DO NOT write about unrelated topics like programming, variables, or JavaScript.
ONLY use the business information provided in the SEARCH RESULTS, DETAILED INFORMATION, and REVIEW SENTIMENT ANALYSIS sections above.

Write a comprehensive, friendly summary that:
1. Directly answers the user's question about "{clarified_query} in {clarified_location}"
2. Highlights the top 3-5 business recommendations from the search results
3. Includes relevant details based on what was requested (ratings, prices, sentiment)
4. Is easy to read and conversational
5. Ends with a helpful closing statement

Do NOT include any information that is not in the data above.
"""
    
    # Generate summary using LLM
    response = llm.invoke([SystemMessage(content=context)])
    final_summary = response.content
    
    return {
        "messages": [AIMessage(content=f"\n\n📝 SUMMARY DRAFT:\n\n{final_summary}")],
        "final_summary": final_summary,
        "next_agent": "supervisor_approval",
        "needs_revision": False  # Reset flag after generating new summary
    }
