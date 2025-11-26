"""Shared prompt templates for Yelp Navigator V1, V2, and V3."""

# ============================================================================
# BASE PROMPT COMPONENTS (for reuse across versions)
# ============================================================================

# Base clarification prompt (used by V2 and V3)
base_clarification_prompt = """You are a helpful assistant that clarifies user requests for business searches.

Your goal is to extract three pieces of information:
1. QUERY: What type of business/food/service are they looking for?
2. LOCATION: Where are they searching?
3. DETAIL_LEVEL: What information do they need?
   - "general": Just basic business info (name, rating, location)
   - "detailed": Include website information and additional details
   - "reviews": Include customer reviews and sentiment analysis

Analyze the user's query and extract this information. If the query is too vague and missing critical information,
you should make reasonable assumptions and proceed rather than asking for clarification.

CRITICAL RULES:
- LOCATION is REQUIRED and MUST NOT be None or empty
- If they say "restaurants" without a location, use "United States" as default
- If they mention a state (e.g., "California"), use that state name (e.g., "California")
- If they mention a city and state (e.g., "bay area"), infer the full location (e.g., "San Francisco Bay Area, California")
- If they don't specify detail level, use "general"
- If they mention wanting "reviews" or "what people say", use "reviews" detail level
- NEVER return None or null for location - always provide a valid location string
"""

# State-aware context template (for follow-up queries in V2 and V3)
def state_aware_context_template(current_query: str, current_location: str) -> str:
    """Generate state-aware context for handling follow-up queries."""
    return f"""
--- CURRENT SEARCH CONTEXT ---
You have already searched for:
- QUERY: "{current_query}"
- LOCATION: "{current_location}"

Search results with ratings are already cached and available.

--- INSTRUCTIONS ---
Analyze the *latest user message* in the context of this CURRENT SEARCH.

**CRITICAL: Distinguish between questions that need NEW data vs questions answerable from CACHED data:**

1.  **Questions answerable from CACHED DATA (use 'general' detail level):**
    - "Which one has the best reviews/ratings?" → Already have ratings, just need to compare
    - "Which is highest rated?" → Already have ratings
    - "What's the top one?" → Already have ratings
    - "Tell me about the best one" → Already have basic info
    - For these: Keep QUERY="{current_query}", LOCATION="{current_location}", DETAIL_LEVEL="general"

2.  **Questions needing NEW DATA (update detail level):**
    - "What do customers say in their reviews?" → Need full review text: DETAIL_LEVEL="reviews"
    - "Show me detailed reviews" → Need sentiment analysis: DETAIL_LEVEL="reviews"
    - "Do they have websites?" → Need website info: DETAIL_LEVEL="detailed"
    - For these: Keep QUERY="{current_query}", LOCATION="{current_location}", update DETAIL_LEVEL

3.  **Completely NEW search:**
    - Extract the new QUERY and LOCATION.
    - Set DETAIL_LEVEL based on their new query (default to "general").
    
4.  **General chat:**
    - Respond as a general chat. (The decision model will handle this).
    
Remember: If the user is asking for a comparison or ranking ("best", "top", "highest"), they want analysis of EXISTING data, not new data fetching.
"""

# Base supervisor instructions (core logic shared by V2 and V3)
base_supervisor_instructions = """
Instructions:
Based on the Target Detail Level and the Current Data We Have, decide the single next action.

1.  If 'Basic Search Results' is False, you MUST call 'search'. This is the first step.
2.  If 'Basic Search Results' is True, check the detail level:
    a.  If Detail Level is 'general': We have enough data. Call 'finalize'.
        - The summary node will handle comparative questions ("which is best?") using cached ratings.
    b.  If Detail Level is 'detailed':
        - If 'Website/Details Data' is False, call 'get_details'.
        - If 'Website/Details Data' is True, we have enough data. Call 'finalize'.
    c.  If Detail Level is 'reviews':
        - If 'Review/Sentiment Data' is False, call 'analyze_sentiment'.
        - If 'Review/Sentiment Data' is True, we have enough data. Call 'finalize'.
        
IMPORTANT: 
- Only call one action at a time.
- Do not call 'get_details' or 'analyze_sentiment' if 'search' has not been run successfully.
- If the user asks comparative questions ("which is best?", "highest rated?"), the existing search data is sufficient - call 'finalize'.
"""

# ============================================================================
# V1 PROMPTS (legacy)
# ============================================================================

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
    
    search_available = "[Available]" if agent_outputs.get("search", {}).get("success") else "[Not available]"
    details_available = "[Available]" if agent_outputs.get("details", {}).get("success") else "[Not available]"
    sentiment_available = "[Available]" if agent_outputs.get("sentiment", {}).get("success") else "[Not available]"
    
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
                               revision_feedback: str = "", user_question: str = "") -> str:
    """Generate the summary generation prompt with all context.
    
    Args:
        user_question: The actual user question to answer (e.g., "Which one has the best reviews?")
    """
    
    context = f"""Create a comprehensive, human-readable summary based on the following information:

            User was looking for: {clarified_query} in {clarified_location}
            Detail level requested: {detail_level}
            """
    
    # Add specific user question context if provided
    if user_question:
        context += f"""
            Specific user question: {user_question}
            
            IMPORTANT: Answer their SPECIFIC QUESTION directly. 
            - If they ask "which is best?" or "highest rated?", compare the ratings and highlight the top one.
            - If they ask "tell me about X", focus on that specific business.
            - Don't just list all results - answer what they asked.
            """
    
    # Add revision feedback if this is a revision
    if needs_revision and revision_feedback:
        context += f"\n*** SUPERVISOR FEEDBACK (please address this): ***\n{revision_feedback}\n"
    
    context += "\nAgent Results:\n"
    
    # Add search results
    if "search" in agent_outputs and agent_outputs["search"].get("success"):
        search = agent_outputs["search"]
        context += f"\n\nSEARCH RESULTS ({search['result_count']} total found):\n"
        for i, biz in enumerate(search.get("businesses", []), 1):
            context += f"{i}. {biz['name']}\n"
            context += f"   Rating: {biz['rating']} stars ({biz['review_count']} reviews)\n"
            context += f"   Price: {biz.get('price_range', 'N/A')}\n"
            context += f"   Categories: {', '.join(biz.get('categories', []))}\n"
            context += f"   Phone: {biz.get('phone', 'N/A')}\n"
            context += f"   Website: {biz.get('website', 'N/A')}\n\n"
    
    # Add details if available
    if "details" in agent_outputs and agent_outputs["details"].get("success"):
        details = agent_outputs["details"]
        context += "\n\nDETAILED INFORMATION:\n"
        for i, biz in enumerate(details.get("businesses_with_details", []), 1):
            context += f"{i}. {biz['name']}\n"
            if biz['has_website_info']:
                context += f"   Website content available ({biz['website_content_length']} characters)\n"
            else:
                context += f"   No website information available\n"
    
    # Add sentiment if available
    if "sentiment" in agent_outputs and agent_outputs["sentiment"].get("success"):
        sentiment = agent_outputs["sentiment"]
        search = agent_outputs.get("search", {})
        
        # Create a mapping from business_id to business name from search results
        business_name_map = {}
        if search.get("success"):
            for business in search.get("businesses", []):
                business_name_map[business.get("id")] = business.get("name", "Unknown Business")
        
        context += "\n\nREVIEW SENTIMENT ANALYSIS:\n"
        for i, biz in enumerate(sentiment.get("sentiment_summaries", []), 1):
            business_id = biz.get('business_id', 'N/A')
            business_name = business_name_map.get(business_id, f"Business ID: {business_id}")
            
            context += f"{i}. {business_name}\n"
            context += f"   Overall Sentiment: {biz.get('overall_sentiment', 'unknown')}\n"
            context += f"   Positive: {biz['positive_count']}, Neutral: {biz['neutral_count']}, Negative: {biz['negative_count']}\n"
            context += f"   Total Reviews Analyzed: {biz.get('total_reviews', 0)}\n"
            
            # Add sample reviews
            if biz.get('highest_rated_reviews'):
                top_review = biz['highest_rated_reviews'][0]
                context += f"   Sample positive review: {top_review.get('text', '')}...\n"
            if biz.get('lowest_rated_reviews'):
                low_review = biz['lowest_rated_reviews'][0]
                context += f"   Sample negative review: {low_review.get('text', '')}...\n"
    
    # Analyze the user question to determine response style
    response_style = "list"  # default - show multiple businesses
    if user_question:
        user_q_lower = user_question.lower()
        # ONLY use focused mode for very specific single-business questions
        # Comparative questions like "best", "top", "highest" should get a ranked list
        if any(phrase in user_q_lower for phrase in ["tell me more about", "what about", "how about", "details about", "info about"]):
            response_style = "focused"
    
    context += f"""\n\nIMPORTANT INSTRUCTIONS:
            You MUST create a summary about the business search results provided above.
            DO NOT write about unrelated topics like programming, variables, or JavaScript.
            ONLY use the business information provided in the SEARCH RESULTS, DETAILED INFORMATION, and REVIEW SENTIMENT ANALYSIS sections above.
            
            ALWAYS include brief context about what makes each business unique or special based on their categories, 
            reviews, or other distinguishing features.
            """
    
    if response_style == "focused":
        context += f"""
            RESPONSE STYLE: FOCUSED ANSWER
            The user asked: "{user_question}"
            
            This is a specific question about ONE business. DO NOT list all results.
            
            Instructions:
            1. Provide a focused answer about the specific business they asked about
            2. YOU MUST include: name, rating, review count, price range, **phone number**, and **website URL**
            3. Format contact info clearly: "Phone: [number]" and "Website: [URL]"
            4. Add 2-3 sentences about what makes this business special (atmosphere, specialties, etc.)
            5. Keep it conversational but brief - 3-5 sentences total
            
            DO NOT list multiple businesses. Answer their SPECIFIC question only.
            """
    else:
        context += f"""
            RESPONSE STYLE: COMPREHENSIVE LIST
            
            Write a comprehensive, friendly summary that:
            1. Directly answers the user's question about "{clarified_query} in {clarified_location}"
            2. If the user asked for "best", "top", or "highest rated", start with the top 2-3 options and explain why they stand out
            3. Then provide a complete list of the top 5 business recommendations from the search results
            4. For EACH business, YOU MUST include ALL of the following in this exact order (if available in the data):
               - Name (bold or highlighted)
               - Rating (X stars) and review count (Y reviews)
               - Price range (if available)
               - **Phone number** (REQUIRED - format as: Phone: XXX-XXX-XXXX)
               - **Website** (REQUIRED - format as: Website: URL)
               - 1-2 sentences describing what makes it unique/special (atmosphere, specialties, customer favorites)
            5. CRITICAL: Phone numbers and website URLs are MANDATORY for each business. Look for these in the search results data under 'phone' and 'website' fields.
            6. Order businesses by a balance of rating AND review count:
               - Prioritize businesses with 4.5+ stars AND substantial review counts (100+ reviews)
               - A 4.5-star business with 2000 reviews is more reliable than a 4.8-star with 10 reviews
               - Balance quality (rating) with validation (review volume)
               - If ratings are close (within 0.2 stars), rank by review count
            7. Is easy to read and conversational
            8. Ends with a helpful closing statement
            
            IMPORTANT: Always show multiple businesses (5), even for "best" or "top" questions. Users want options to choose from.
            """
    
    context += """
            
            CRITICAL FORMATTING REQUIREMENTS:
            - You MUST include phone numbers for every business (found in the 'phone' field of search results)
            - You MUST include website URLs for every business (found in the 'website' field of search results)
            - If phone or website shows 'N/A' in the data, state "Contact information not available" but this should be rare
            - Format phone numbers clearly: "Phone: +1-XXX-XXX-XXXX" or similar
            - Format websites as clickable links or clear URLs: "Website: https://..."
            
            Do NOT include any information that is not in the data above.
            Do NOT skip phone numbers or websites - they are essential contact information for users.
            """
    
    return context
