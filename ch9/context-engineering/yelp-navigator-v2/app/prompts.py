

# System prompt for clarification
clarification_prompt = """You are a helpful assistant that clarifies user requests for business searches.

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

# System prompt for supervisor approval
def supervisor_approval_prompt(clarified_query: str, clarified_location: str, detail_level: str, 
                                agent_outputs: dict, final_summary: str) -> str:
    """Generate the supervisor approval prompt with current state information."""
    
    search_available = "✓ Available" if agent_outputs.get("search", {}).get("success") else "✗ Not available"
    details_available = "✓ Available" if agent_outputs.get("details", {}).get("success") else "✗ Not available"
    sentiment_available = "✓ Available" if agent_outputs.get("sentiment", {}).get("success") else "✗ Not available"
    
    return f"""You are a supervisor reviewing a summary for quality and completeness.

USER REQUEST:
- Query: {clarified_query} in {clarified_location}
- Detail level: {detail_level}

AVAILABLE DATA:
- Search results: {search_available}
- Website details: {details_available}
- Review sentiment: {sentiment_available}

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

# System prompt for summary generation
def summary_generation_prompt(clarified_query: str, clarified_location: str, detail_level: str,
                               agent_outputs: dict, needs_revision: bool = False, 
                               revision_feedback: str = "") -> str:
    """Generate the summary generation prompt with all context."""
    
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
    
    context += f"""\n\nIMPORTANT INSTRUCTIONS:
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
    
    return context

