"""
Pipeline 1 Wrapper for Hayhooks

This wrapper loads the serialized Pipeline 1 (Business Search with NER) 
and provides API endpoints for use with Hayhooks.
"""

from typing import List, Dict, Any
import os
import sys
from pathlib import Path

from hayhooks import BasePipelineWrapper, log, get_last_user_message
from haystack import Pipeline

# Add parent directory to path for imports
current_dir = Path(__file__).parent
if str(current_dir.parent.parent) not in sys.path:
    sys.path.insert(0, str(current_dir.parent.parent))


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        """Initialize Pipeline 1: Business Search with NER"""
        log.info("Setting up Pipeline 1: Business Search with NER...")
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Load the serialized pipeline
        pipeline_yaml = (Path(__file__).parent / "pipeline1_business_search_ner.yaml").read_text()
        self.pipeline = Pipeline.loads(pipeline_yaml)
        
        # Reinitialize the YelpBusinessSearch component with the API key
        rapid_api_key = os.getenv("RAPID_API_KEY")
        if not rapid_api_key:
            log.warning("RAPID_API_KEY not found in environment variables")
        else:
            log.info(f"Loaded RAPID_API_KEY (length: {len(rapid_api_key)} chars)")
            # Get the existing component and set its api_key
            yelp_search_component = self.pipeline.get_component("yelp_search")
            yelp_search_component.api_key = rapid_api_key
            yelp_search_component.headers = {
                "x-rapidapi-key": rapid_api_key,
                "x-rapidapi-host": "yelp-business-reviews.p.rapidapi.com"
            }
            log.info("Successfully injected API key into YelpBusinessSearch component")
        
        log.info("Pipeline 1 setup complete")
    
    def run_api(self, query: str) -> Dict[str, Any]:
        """
        Search for businesses on Yelp using natural language query.
        
        This API endpoint:
        1. Accepts a natural language query (e.g., "cheese shops in Madison, WI")
        2. Extracts entities (locations, keywords) using NER
        3. Searches Yelp API for matching businesses
        4. Returns business information including IDs, names, ratings, etc.
        
        Args:
            query: Natural language search query
            
        Returns:
            Dictionary with search results and metadata
        """
        log.info(f"Processing business search query: {query}")
        
        try:
            # Run the pipeline with the query
            pipeline_inputs = {
                "query_converter": {"query": query}
            }
            
            log.info("Running Pipeline 1...")
            result = self.pipeline.run(
                pipeline_inputs,
                include_outputs_from={"query_converter", "ner_extractor", "keyword_extractor", "yelp_search"}
            )
            
            # Extract search results
            yelp_results = result.get("yelp_search", {})
            search_results = yelp_results.get("results", {})
            search_params = yelp_results.get("search_params", {})
            
            # Get extracted entities from keyword extractor
            keyword_extraction = result.get("keyword_extractor", {})
            
            # Handle both list and single value formats for backward compatibility
            locations = keyword_extraction.get("locations", [])
            keywords = keyword_extraction.get("keywords", [])
            original_queries = keyword_extraction.get("original_queries", [])
            
            # For backward compatibility, provide single values if only one query
            extracted_location = locations[0] if len(locations) == 1 else locations
            extracted_keywords = keywords[0] if len(keywords) == 1 else keywords
            
            # Format the response
            businesses = search_results.get("results", [])
            result_count = search_results.get("resultCount", 0)
            
            response = {
                "query": query,
                "extracted_location": extracted_location,
                "extracted_keywords": extracted_keywords,
                "extracted_locations": locations,  # Include full list for multi-query
                "extracted_keywords_list": keywords,  # Include full list for multi-query
                "original_queries": original_queries,
                "search_params": search_params,
                "result_count": result_count,
                "is_multi_query": search_results.get("aggregated", False),
                "total_searches": search_results.get("total_searches", 1),
                "businesses": [
                    {
                        "business_id": biz.get("bizId"),
                        "name": biz.get("name"),
                        "alias": biz.get("alias"),
                        "rating": biz.get("rating"),
                        "review_count": biz.get("reviewCount"),
                        "categories": biz.get("categories", []),
                        "price_range": biz.get("priceRange"),
                        "phone": biz.get("phone"),
                        "website": biz.get("website"),
                        "location": {
                            "lat": biz.get("lat"),
                            "lon": biz.get("lon")
                        },
                        "images": biz.get("images", [])
                    }
                    for biz in businesses
                ]
            }
            
            log.info(f"Query processed successfully - {result_count} businesses found")
            return response
            
        except Exception as e:
            log.error(f"Error processing query: {str(e)}")
            return {
                "error": str(e),
                "query": query,
                "result_count": 0,
                "businesses": []
            }
    
    def run_chat_completion(self, model: str, messages: list, body: dict) -> str:
        """
        OpenAI-compatible chat completion endpoint.
        
        This allows the pipeline to be used in chat interfaces by converting
        the business search results into a natural language response.
        """
        # Extract the user's question from messages
        question = get_last_user_message(messages)
        
        # Run the pipeline
        result = self.run_api(query=question)
        
        # Format as natural language response
        if result.get("error"):
            return f"I encountered an error searching for businesses: {result['error']}"
        
        result_count = result.get("result_count", 0)
        businesses = result.get("businesses", [])
        
        if result_count == 0:
            return f"I couldn't find any businesses matching '{question}'."
        
        # Create a natural language response
        response_lines = [
            f"I found {result_count} business(es) for '{question}':",
            ""
        ]
        
        for i, biz in enumerate(businesses[:5], 1):  # Limit to top 5 for chat
            response_lines.append(f"{i}. **{biz['name']}**")
            if biz.get('rating'):
                response_lines.append(f"   - Rating: {biz['rating']}/5 ({biz['review_count']} reviews)")
            if biz.get('categories'):
                response_lines.append(f"   - Categories: {', '.join(biz['categories'][:3])}")
            if biz.get('price_range'):
                response_lines.append(f"   - Price: {biz['price_range']}")
            if biz.get('phone'):
                response_lines.append(f"   - Phone: {biz['phone']}")
            response_lines.append("")
        
        return "\n".join(response_lines)
