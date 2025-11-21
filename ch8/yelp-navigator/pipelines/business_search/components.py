"""
Custom components for Pipeline 1: Business Search with NER

This module contains reusable custom components that can be imported
by both the pipeline builder script and the Hayhooks wrapper.
"""

import requests
from haystack import component, Document
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@component
class QueryToDocument:
    """
    Converts a natural language query string into Haystack Documents.
    This component can handle both simple and complex multi-part queries.
    
    Complex queries with multiple location/item pairs (e.g., "coffee in Vancouver and wine in LA")
    are split into separate documents for parallel processing.
    
    Input:
        - query (str): Natural language query from user
    
    Output:
        - documents (List[Document]): One or more documents (one per sub-query)
    """
    
    def __init__(self):
        """Initialize the component with a logger."""
        self.logger = logging.getLogger(__name__ + ".QueryToDocument")
    
    @component.output_types(documents=List[Document])
    def run(self, query: str) -> Dict[str, List[Document]]:
        """
        Convert query string to Document object(s).
        Detects compound queries using multiple strategies:
        1. ' and ' separator (e.g., "coffee in Vancouver and pizza in LA")
        2. Comma-separated items before location (e.g., "coffee, cheese in Vancouver")
        3. Multiple locations in a single query (handled downstream)
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary with 'documents' key containing one document per sub-query
        """
        self.logger.info(f"Converting query to document(s): '{query}'")
        
        # Strategy 1: Split on " and " to detect multiple queries
        # Match patterns like "X in Y and Z in W"
        sub_queries = [q.strip() for q in query.split(' and ') if q.strip()]
        
        # Only split if we have multiple parts that look like separate requests
        # (each should ideally have "in" or "for" indicating location/item pairs)
        if len(sub_queries) > 1:
            # Check if sub-queries look like independent location queries
            location_indicators = ['in ', 'for ', 'near ', 'at ']
            valid_sub_queries = [
                sq for sq in sub_queries 
                if any(indicator in sq.lower() for indicator in location_indicators)
            ]
            
            if len(valid_sub_queries) > 1:
                self.logger.info(f"Detected {len(valid_sub_queries)} sub-queries via ' and ' separator")
                documents = [Document(content=sq) for sq in valid_sub_queries]
                for i, doc in enumerate(documents):
                    self.logger.debug(f"Created document {i+1} with ID: {doc.id} - Content: '{doc.content}'")
                return {"documents": documents}
        
        # Strategy 2: Check for comma-separated items before location
        # Pattern: "item1, item2 in location1, location2"
        # This will be handled as a single document, but EntityKeywordExtractor will split by locations
        import re
        location_pattern = r'\b(?:in|near|at|for)\b'
        match = re.search(location_pattern, query.lower())
        
        if match:
            # Split at location indicator
            location_word_start = match.start()
            items_part = query[:location_word_start].strip()
            location_part = query[location_word_start:].strip()
            
            # Check if items part has commas (multiple items)
            if ',' in items_part:
                self.logger.info(f"Detected comma-separated items: '{items_part}' with locations: '{location_part}'")
                # Return as single document - EntityKeywordExtractor will handle multiple locations
        
        # Single query - treat as one document
        self.logger.info("Processing as single query (may contain multiple locations)")
        doc = Document(content=query)
        self.logger.debug(f"Created document with ID: {doc.id}")
        return {"documents": [doc]}


@component
class EntityKeywordExtractor:
    """
    Extracts location and keywords from documents with named entities.
    
    This component processes documents that have been annotated by Haystack's 
    NamedEntityExtractor. It reads NamedEntityAnnotation objects from the 
    document metadata and extracts location and keyword information.
    
    This component:
    1. Identifies location entities (LOC) from NER results
    2. Collects other entities (ORG, MISC) as keywords
    3. Combines with original query terms
    4. Returns structured location and keyword data for each document
    5. Supports both single and multiple documents (for multi-query support)
    
    Input:
        - documents (List[Document]): Documents with named_entities in metadata
          (output from NamedEntityExtractor)
    
    Output:
        - locations (List[str]): Extracted locations for Yelp search (one per document)
        - keywords (List[List[str]]): Search keywords (one list per document)
        - original_queries (List[str]): Original queries (one per document)
    """
    
    def __init__(self):
        """Initialize the component with a logger."""
        self.logger = logging.getLogger(__name__ + ".EntityKeywordExtractor")
    
    @component.output_types(
        locations=List[str],
        keywords=List[List[str]],
        original_queries=List[str]
    )
    def run(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Extract location and keywords from NER-processed documents.
        
        This method processes NamedEntityAnnotation objects stored in the 
        document's metadata by Haystack's NamedEntityExtractor.
        Handles multiple documents for multi-query support.
        
        Args:
            documents: List of documents with named_entities metadata
            
        Returns:
            Dictionary containing lists of locations, keywords, and original queries
        """
        if not documents:
            self.logger.warning("No documents provided for entity extraction")
            return {
                "locations": [],
                "keywords": [],
                "original_queries": []
            }
        
        all_locations = []
        all_keywords = []
        all_original_queries = []
        
        # Process each document separately
        for doc_idx, doc in enumerate(documents):
            original_query = doc.content
            all_original_queries.append(original_query)
            self.logger.info(f"Processing document {doc_idx + 1}/{len(documents)}: '{original_query}'")
            
            # Get NamedEntityAnnotation objects from document metadata
            # These are added by Haystack's NamedEntityExtractor
            named_entities = doc.meta.get("named_entities", [])
            self.logger.debug(f"Found {len(named_entities)} named entities in document {doc_idx + 1}")
            
            locations = []
            keywords = []
            
            # Process each NamedEntityAnnotation
            for annotation in named_entities:
                # Extract the entity text from the document content using start/end indices
                entity_text = doc.content[annotation.start:annotation.end]
                entity_label = annotation.entity
                confidence = annotation.score
                
                self.logger.debug(f"Entity: '{entity_text}' - Type: {entity_label} - Confidence: {confidence:.3f}")
                
                # Only use high-confidence entities (>0.7)
                if confidence > 0.7:
                    # Check if it's a location entity
                    if entity_label == "LOC":
                        locations.append(entity_text)
                        self.logger.info(f"Extracted location: '{entity_text}'")
                    # Use organizations and miscellaneous entities as keywords
                    elif entity_label in ["ORG", "MISC"]:
                        keywords.append(entity_text)
                        self.logger.info(f"Extracted keyword: '{entity_text}' ({entity_label})")
            
            # Handle multiple locations
            if len(locations) > 1:
                # Multiple locations detected - create separate searches for each
                self.logger.info(f"Multiple locations detected in document {doc_idx + 1}: {locations}")
                
                # Combine keywords with query terms (remove common stop words)
                stop_words = ["the", "in", "for", "a", "an", "best", "good", "great", "town", "and", "or"]
                query_words = [word for word in original_query.split() 
                              if word.lower() not in stop_words and word not in locations]
                
                # Merge and deduplicate keywords
                doc_keywords = list(set(keywords + query_words))
                
                # Create one search per location with the same keywords
                for loc in locations:
                    self.logger.info(f"Creating search - Location: '{loc}', Keywords: {doc_keywords}")
                    all_locations.append(loc)
                    all_keywords.append(doc_keywords)
                    all_original_queries.append(f"{', '.join(doc_keywords)} in {loc}")
                
                # Skip adding the original query since we've split it
                all_original_queries.pop()  # Remove the one added at the start of the loop
            else:
                # Single location or no location
                location = locations[0] if locations else ""
                if not location:
                    self.logger.warning(f"No location extracted from document {doc_idx + 1}")
                
                # Combine keywords with query terms (remove common stop words)
                stop_words = ["the", "in", "for", "a", "an", "best", "good", "great", "town"]
                query_words = [word for word in original_query.split() 
                              if word.lower() not in stop_words]
                
                # Merge and deduplicate keywords
                doc_keywords = list(set(keywords + query_words))
                
                self.logger.info(f"Document {doc_idx + 1} extraction - Location: '{location}', Keywords: {doc_keywords}")
                
                all_locations.append(location)
                all_keywords.append(doc_keywords)
        
        self.logger.info(f"Completed extraction for {len(documents)} document(s)")
        
        return {
            "locations": all_locations,
            "keywords": all_keywords,
            "original_queries": all_original_queries
        }


@component
class YelpBusinessSearch:
    """
    Searches for businesses using the Yelp Business Reviews API.
    
    This component:
    1. Accepts locations and keywords from previous component (supports multiple queries)
    2. Constructs API request with proper headers and parameters
    3. Executes searches via RapidAPI (one per location/keyword pair)
    4. Aggregates and returns parsed JSON results with business information
    
    Input:
        - locations (List[str]): Geographic locations to search (one per sub-query)
        - keywords (List[List[str]]): Search keywords (one list per sub-query)
        - original_queries (List[str]): Original queries (one per sub-query)
    
    Output:
        - results (Dict): Aggregated JSON response with all businesses
        - search_params (Dict): The parameters used for all searches
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Yelp search component.
        
        Args:
            api_key: RapidAPI key for Yelp Business Reviews API
        """
        self.api_key = api_key
        self.base_url = "https://yelp-business-reviews.p.rapidapi.com/search"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "yelp-business-reviews.p.rapidapi.com"
        }
        self.logger = logging.getLogger(__name__ + ".YelpBusinessSearch")
    
    @component.output_types(
        results=Dict,
        search_params=Dict
    )
    def run(self, locations: List[str], keywords: List[List[str]], original_queries: List[str]) -> Dict[str, Any]:
        """
        Execute Yelp business search(es).
        Handles both single and multiple location/keyword pairs.
        
        Args:
            locations: List of locations to search in
            keywords: List of keyword lists (one per location)
            original_queries: List of original queries
            
        Returns:
            Dictionary with aggregated API results and search parameters
        """
        if not locations or not keywords or not original_queries:
            self.logger.error("Empty input provided to YelpBusinessSearch")
            return {
                "results": {"error": "Empty input", "resultCount": 0, "results": []},
                "search_params": {"searches": []}
            }
        
        # Ensure all lists have the same length
        num_queries = min(len(locations), len(keywords), len(original_queries))
        if num_queries == 0:
            self.logger.error("No valid queries to process")
            return {
                "results": {"error": "No valid queries", "resultCount": 0, "results": []},
                "search_params": {"searches": []}
            }
        
        all_businesses = []
        search_details = []
        total_results = 0
        
        # Execute search for each location/keyword pair
        for i in range(num_queries):
            location = locations[i] if locations[i] else "United States"
            keyword_list = keywords[i]
            original_query = original_queries[i]
            
            if not location:
                location = "United States"
                self.logger.warning(f"Query {i+1}: No location provided, using fallback: '{location}'")
            
            # Construct query string from keywords
            query_string = " ".join(keyword_list) if keyword_list else original_query
            
            # Build query parameters
            querystring = {
                "location": location,
                "query": query_string
            }
            
            self.logger.info(f"Query {i+1}/{num_queries} - Searching Yelp API - Location: '{location}', Query: '{query_string}'")
            
            try:
                # Execute API request
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params=querystring
                )
                
                self.logger.debug(f"Query {i+1}: API response status: {response.status_code}")
                
                # Parse JSON response
                result = response.json()
                
                result_count = result.get('resultCount', 0)
                businesses = result.get('results', [])
                
                self.logger.info(f"Query {i+1}: Successfully retrieved {result_count} businesses")
                
                # Add businesses to aggregated list
                all_businesses.extend(businesses)
                total_results += result_count
                
                # Track search parameters
                search_details.append({
                    "location": location,
                    "query": query_string,
                    "original_query": original_query,
                    "result_count": result_count
                })
                
            except Exception as e:
                self.logger.error(f"Query {i+1}: Error during Yelp API search: {str(e)}")
                search_details.append({
                    "location": location,
                    "query": query_string,
                    "original_query": original_query,
                    "error": str(e),
                    "result_count": 0
                })
        
        self.logger.info(f"Completed all searches. Total businesses retrieved: {len(all_businesses)}")
        
        # Return aggregated results in expected format
        return {
            "results": {
                "resultCount": len(all_businesses),
                "results": all_businesses,
                "total_searches": num_queries,
                "aggregated": num_queries > 1
            },
            "search_params": {
                "searches": search_details,
                "combined_query": " AND ".join(original_queries)
            }
        }
