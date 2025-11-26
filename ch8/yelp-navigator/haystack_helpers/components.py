import requests
from typing import Optional

# Haystack Imports
from haystack import component
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage

from .state import YelpAgentState

# Hayhooks Configuration
BASE_URL = "http://localhost:1416"

# ===============================================================================
# 2. HELPER COMPONENTS (Multiplexers)
# ===============================================================================

@component
class StateMultiplexer:
    """
    A helper component that accepts state from multiple possible upstream sources
    and passes the first valid one downstream. Essential for nodes that have 
    multiple incoming edges (e.g., from Clarifier AND from Supervisor loop-back).
    """
    def __init__(self, name: str = "Multiplexer"):
        self.name = name

    @component.output_types(state=YelpAgentState)
    def run(self, 
            source_1: Optional[YelpAgentState] = None, 
            source_2: Optional[YelpAgentState] = None,
            source_3: Optional[YelpAgentState] = None,
            source_4: Optional[YelpAgentState] = None):
        
        # Return the first non-None state found
        active_state = source_1 or source_2 or source_3 or source_4
        if not active_state:
            # This happens if the pipeline is starting or a branch was skipped
            return {}
            
        print(f"🔀 [{self.name}] Forwarding state...")
        return {"state": active_state}

# ===============================================================================
# 3. WORKER COMPONENTS (The Nodes)
# ===============================================================================

@component
class ClarificationComponent:
    """
    Clarifies user intent and extracts query, location, and detail level.
    """
    def __init__(self):
        self.generator = OpenAIChatGenerator(model="gpt-4o")

    @component.output_types(state=YelpAgentState)
    def run(self, query: str):
        print(f"\n🧠 [Clarification] Processing: {query}")
        
        # Create initial state
        state = YelpAgentState()
        state.user_query = query
        
        # Force defaults after 2 attempts
        if state.clarification_attempts >= 2:
            state.clarified_query = "restaurants"
            state.clarified_location = "United States"
            state.detail_level = "general"
            state.clarification_complete = True
            state.add_message("Using defaults: restaurants in United States, general detail level.")
            return {"state": state}
        
        # Use LLM to extract information
        system_prompt = """Extract query, location, and detail level from user request.
                        Detail levels: 'general' (basic info), 'detailed' (websites), 'reviews' (sentiment).
                        Use defaults if unclear: restaurants, United States, general.

                        Respond in this format when ready:
                        CLARIFIED:
                        QUERY: [search term]
                        LOCATION: [location]
                        DETAIL_LEVEL: [general/detailed/reviews]"""
        
        messages = [
            ChatMessage.from_system(system_prompt),
            ChatMessage.from_user(query)
        ]
        
        response = self.generator.run(messages=messages)
        response_text = response["replies"][0].text
        
        if "CLARIFIED:" in response_text:
            info = {}
            for line in response_text.split('\n'):
                if line.startswith("QUERY:"): 
                    info['query'] = line.replace("QUERY:", "").strip()
                elif line.startswith("LOCATION:"): 
                    info['location'] = line.replace("LOCATION:", "").strip()
                elif line.startswith("DETAIL_LEVEL:"): 
                    info['detail_level'] = line.replace("DETAIL_LEVEL:", "").strip()
            
            state.clarified_query = info.get('query', 'restaurants')
            state.clarified_location = info.get('location', 'United States')
            state.detail_level = info.get('detail_level', 'general')
            state.clarification_complete = True
            state.add_message(f"Clarified: {state.clarified_query} in {state.clarified_location} ({state.detail_level})")
        else:
            state.clarification_attempts += 1
            state.add_message("Clarification incomplete. Please try again.")
        
        return {"state": state}


@component
class SearchComponent:
    """
    Search agent that finds businesses using Hayhooks API.
    """
    def __init__(self):
        pass

    @component.output_types(to_details=YelpAgentState, to_summary=YelpAgentState)
    def run(self, state: YelpAgentState):
        print(f"\n🔍 [Search] Looking for: {state.clarified_query} in {state.clarified_location}")
        
        # Call real Hayhooks search tool
        full_query = f"{state.clarified_query} in {state.clarified_location}"
        try:
            response = requests.post(
                f"{BASE_URL}/business_search/run",
                json={"query": full_query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                businesses = result.get('businesses', [])
                
                search_output = {
                    "success": True,
                    "result_count": result.get('result_count', 0),
                    "extracted_location": result.get('extracted_location', ''),
                    "extracted_keywords": result.get('extracted_keywords', []),
                    "businesses": [{
                        "id": b.get('id'), "name": b.get('name'), "rating": b.get('rating'),
                        "review_count": b.get('review_count'), "categories": b.get('categories', []),
                        "price_range": b.get('price_range', 'N/A'), "phone": b.get('phone', 'N/A'),
                    } for b in businesses[:10]],
                    "full_output": data
                }
                
                summary = f"Found {search_output['result_count']} businesses:\n"
                summary += "\n".join(f"{i}. {b['name']} - {b['rating']} stars ({b['review_count']} reviews)" 
                                   for i, b in enumerate(search_output['businesses'][:5], 1))
                
                state.agent_outputs["search"] = search_output
                state.add_message(summary)
                
                # Route based on detail level
                if state.detail_level in ["detailed", "reviews"]:
                    return {"to_details": state}
                else:
                    return {"to_summary": state}
            else:
                state.agent_outputs["search"] = {"success": False, "error": f"HTTP {response.status_code}"}
                state.add_message(f"Search failed: HTTP {response.status_code}")
                return {"to_summary": state}
                
        except Exception as e:
            state.agent_outputs["search"] = {"success": False, "error": str(e)}
            state.add_message(f"Search error: {e}")
            return {"to_summary": state}


@component
class DetailsComponent:
    """
    Details agent that fetches website information using Hayhooks API.
    """
    def __init__(self):
        pass

    @component.output_types(to_sentiment=YelpAgentState, to_summary=YelpAgentState)
    def run(self, state: YelpAgentState):
        print(f"\n🌐 [Details] Fetching website info...")
        
        search_output = state.agent_outputs.get("search", {})
        
        if not search_output.get("success"):
            state.add_message("Skipping details - no search results")
            return {"to_summary": state}
        
        try:
            response = requests.post(
                f"{BASE_URL}/business_details/run",
                json={"pipeline1_output": search_output.get("full_output", {})},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get('metadata_enricher', {}).get('documents', [])
                
                details_output = {
                    "success": True,
                    "document_count": len(documents),
                    "businesses_with_details": [{
                        "name": doc.meta.get('name', 'Unknown'),
                        "has_website_info": bool(doc.meta.get('website_info')),
                        "website_snippet": doc.meta.get('website_info', {}).get('content', '')[:100] if doc.meta.get('website_info') else None
                    } for doc in documents]
                }
                
                state.agent_outputs["details"] = details_output
                state.add_message(f"Retrieved details for {details_output['document_count']} businesses")
                
                # Route based on detail level
                if state.detail_level == "reviews":
                    return {"to_sentiment": state}
                else:
                    return {"to_summary": state}
            else:
                state.agent_outputs["details"] = {"success": False, "error": f"HTTP {response.status_code}"}
                state.add_message(f"Details fetch failed: HTTP {response.status_code}")
                return {"to_summary": state}
                
        except Exception as e:
            state.agent_outputs["details"] = {"success": False, "error": str(e)}
            state.add_message(f"Details error: {e}")
            return {"to_summary": state}


@component
class SentimentComponent:
    """
    Sentiment agent that analyzes reviews using Hayhooks API.
    """
    def __init__(self):
        pass

    @component.output_types(to_summary=YelpAgentState)
    def run(self, state: YelpAgentState):
        print(f"\n💭 [Sentiment] Analyzing reviews...")
        
        search_output = state.agent_outputs.get("search", {})
        
        if not search_output.get("success"):
            state.add_message("Skipping sentiment - no search results")
            return {"to_summary": state}
        
        try:
            response = requests.post(
                f"{BASE_URL}/business_sentiment/run",
                json={"pipeline1_output": search_output.get("full_output", {})},
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                summaries = data.get('sentiment_summarizer', {}).get('sentiment_summaries', [])
                
                sentiment_output = {
                    "success": True,
                    "sentiment_summaries": [{
                        "business_id": s.get('business_id'),
                        "positive_count": s.get('positive_count', 0),
                        "neutral_count": s.get('neutral_count', 0),
                        "negative_count": s.get('negative_count', 0),
                        "highest_rated_reviews": s.get('highest_rated_reviews', [])[:2]
                    } for s in summaries]
                }
                
                state.agent_outputs["sentiment"] = sentiment_output
                state.add_message(f"Analyzed sentiment for {len(sentiment_output['sentiment_summaries'])} businesses")
            else:
                state.agent_outputs["sentiment"] = {"success": False, "error": f"HTTP {response.status_code}"}
                state.add_message(f"Sentiment analysis failed: HTTP {response.status_code}")
                
        except Exception as e:
            state.agent_outputs["sentiment"] = {"success": False, "error": str(e)}
            state.add_message(f"Sentiment error: {e}")
        
        return {"to_summary": state}


@component
class SummaryComponent:
    """
    Summarizer that creates a friendly response using LLM.
    """
    def __init__(self):
        self.generator = OpenAIChatGenerator(model="gpt-4o")

    @component.output_types(state=YelpAgentState)
    def run(self, state: YelpAgentState):
        print(f"\n📝 [Summary] Generating summary...")
        
        agent_outputs = state.agent_outputs
        
        context = f"""Create a friendly summary for: {state.clarified_query} in {state.clarified_location} (detail: {state.detail_level})
"""
        if state.needs_revision and state.revision_feedback:
            context += f"\nADDRESS THIS FEEDBACK: {state.revision_feedback}\n"
        
        # Add search results
        if "search" in agent_outputs and agent_outputs["search"].get("success"):
            search = agent_outputs["search"]
            context += f"\n\nFOUND {search['result_count']} BUSINESSES:\n"
            for i, biz in enumerate(search.get("businesses", [])[:5], 1):
                context += f"{i}. {biz['name']} - {biz['rating']} stars ({biz['review_count']} reviews) - {biz.get('price_range', 'N/A')}\n"
        
        # Add details if available
        if "details" in agent_outputs and agent_outputs["details"].get("success"):
            context += "\n\nWEBSITE INFO:\n"
            for i, biz in enumerate(agent_outputs["details"].get("businesses_with_details", []), 1):
                status = "Has website" if biz['has_website_info'] else "No website"
                context += f"{i}. {biz['name']} - {status}\n"
        
        # Add sentiment if available
        if "sentiment" in agent_outputs and agent_outputs["sentiment"].get("success"):
            search = agent_outputs.get("search", {})
            id_to_name = {b.get('id'): b.get('name', 'Unknown') for b in search.get("businesses", [])}
            context += "\n\nREVIEW SENTIMENT:\n"
            for i, biz in enumerate(agent_outputs["sentiment"].get("sentiment_summaries", []), 1):
                name = id_to_name.get(biz.get('business_id'), f"Business {biz.get('business_id')}")
                context += f"{i}. {name} - +{biz['positive_count']} ={biz['neutral_count']} -{biz['negative_count']}\n"
                if biz.get('highest_rated_reviews'):
                    context += f"   Best: {biz['highest_rated_reviews'][0].get('text', '')[:100]}...\n"
        
        context += "\n\nWrite a friendly, conversational summary with top recommendations."
        
        messages = [ChatMessage.from_system(context)]
        response = self.generator.run(messages=messages)
        state.final_summary = response["replies"][0].text
        state.needs_revision = False
        
        return {"state": state}


@component
class SupervisorComponent:
    """
    The Loop Closer.
    Decides if the summary is approved or needs revision.
    Routes back to: Search, Details, Sentiment, Summary OR finishes.
    """
    def __init__(self):
        self.generator = OpenAIChatGenerator(model="gpt-4o")

    @component.output_types(
        approved=YelpAgentState, 
        revise_search=YelpAgentState,
        revise_details=YelpAgentState,
        revise_sentiment=YelpAgentState,
        revise_summary=YelpAgentState
    )
    def run(self, state: YelpAgentState):
        print(f"👮 [Supervisor] Reviewing (Attempt {state.approval_attempts + 1})...")
        
        # Limit approval attempts
        if state.approval_attempts >= 2:
            print("⚠️ [Supervisor] Approval limit reached. Accepting current summary.")
            state.approval_attempts += 1
            return {"approved": state}
        
        # Use LLM to evaluate summary
        evaluation_prompt = f"""Review this summary for completeness and quality.
                        User request: {state.clarified_query} in {state.clarified_location} (detail: {state.detail_level})

                        SUMMARY:
                        {state.final_summary}

                        Respond with either:
                        APPROVED

                        Or:
                        NEEDS_REVISION
                        FEEDBACK: [what to improve]
                        RERUN_AGENT: [search/details/sentiment/summary]"""
        
        messages = [ChatMessage.from_system(evaluation_prompt)]
        response = self.generator.run(messages=messages)
        evaluation = response["replies"][0].text
        
        # State Update
        state.approval_attempts += 1

        if "APPROVED" in evaluation and "NEEDS_REVISION" not in evaluation:
            print("✅ [Supervisor] Approved!")
            state.add_message("Summary approved!")
            return {"approved": state}
        else:
            # Parse revision request
            feedback, rerun_agent = "", "summary"
            
            for line in evaluation.split('\n'):
                if line.startswith("FEEDBACK:"): 
                    feedback = line.replace("FEEDBACK:", "").strip()
                elif line.startswith("RERUN_AGENT:"): 
                    agent = line.replace("RERUN_AGENT:", "").strip().lower()
                    if agent in ["search", "details", "sentiment", "summary"]: 
                        rerun_agent = agent
            
            print(f"❌ [Supervisor] Needs revision: {feedback}. Rerunning {rerun_agent}.")
            
            # State Update
            state.needs_revision = True
            state.revision_feedback = feedback or "Improve quality"
            state.add_message(f"Needs revision: {feedback}. Re-running {rerun_agent}...")
            
            # Dynamic Routing based on 'rerun_agent' decision
            if rerun_agent == "search": 
                return {"revise_search": state}
            if rerun_agent == "details": 
                return {"revise_details": state}
            if rerun_agent == "sentiment": 
                return {"revise_sentiment": state}
            
            return {"revise_summary": state}
