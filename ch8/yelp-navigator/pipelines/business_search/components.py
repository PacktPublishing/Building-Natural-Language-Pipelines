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
    Converts a natural language query string into a Haystack Document.
    This allows the query to be processed by NER and other document-based components.
    
    Input:
        - query (str): Natural language query from user
    
    Output:
        - documents (List[Document]): Single document containing the query
    """
    
    def __init__(self):
        """Initialize the component with a logger."""
        self.logger = logging.getLogger(__name__ + ".QueryToDocument")
    
    @component.output_types(documents=List[Document])
    def run(self, query: str) -> Dict[str, List[Document]]:
        """
        Convert query string to Document object.
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary with 'documents' key containing the query as a Document
        """
        self.logger.info(f"Converting query to document: '{query}'")
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
    4. Returns structured location and keyword data
    
    Input:
        - documents (List[Document]): Documents with named_entities in metadata
          (output from NamedEntityExtractor)
    
    Output:
        - location (str): Extracted location for Yelp search
        - keywords (List[str]): Search keywords
        - original_query (str): Original user query
    """
    
    def __init__(self):
        """Initialize the component with a logger."""
        self.logger = logging.getLogger(__name__ + ".EntityKeywordExtractor")
    
    @component.output_types(
        location=str,
        keywords=List[str],
        original_query=str
    )
    def run(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Extract location and keywords from NER-processed documents.
        
        This method processes NamedEntityAnnotation objects stored in the 
        document's metadata by Haystack's NamedEntityExtractor.
        
        Args:
            documents: List of documents with named_entities metadata
            
        Returns:
            Dictionary containing location, keywords, and original query
        """
        if not documents:
            self.logger.warning("No documents provided for entity extraction")
            return {
                "location": "",
                "keywords": [],
                "original_query": ""
            }
        
        doc = documents[0]
        original_query = doc.content
        self.logger.info(f"Processing query: '{original_query}'")
        
        # Get NamedEntityAnnotation objects from document metadata
        # These are added by Haystack's NamedEntityExtractor
        named_entities = doc.meta.get("named_entities", [])
        self.logger.debug(f"Found {len(named_entities)} named entities")
        
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
        
        # Use first location found, or default to empty
        location = locations[0] if locations else ""
        if not location:
            self.logger.warning("No location extracted from entities")
        
        # Combine keywords with query terms (remove common stop words)
        stop_words = ["the", "in", "for", "a", "an", "best", "good", "great", "town"]
        query_words = [word for word in original_query.split() 
                      if word.lower() not in stop_words]
        
        # Merge and deduplicate keywords
        all_keywords = list(set(keywords + query_words))
        
        self.logger.info(f"Final extraction - Location: '{location}', Keywords: {all_keywords}")
        
        return {
            "location": location,
            "keywords": all_keywords,
            "original_query": original_query
        }


@component
class YelpBusinessSearch:
    """
    Searches for businesses using the Yelp Business Reviews API.
    
    This component:
    1. Accepts location and keywords from previous component
    2. Constructs API request with proper headers and parameters
    3. Executes the search via RapidAPI
    4. Returns parsed JSON results with business information
    
    Input:
        - location (str): Geographic location to search
        - keywords (List[str]): Search keywords
        - original_query (str): Original user query
    
    Output:
        - results (Dict): JSON response from Yelp API
        - search_params (Dict): The parameters used for the search
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
    def run(self, location: str, keywords: List[str], original_query: str) -> Dict[str, Any]:
        """
        Execute Yelp business search.
        
        Args:
            location: Location to search in
            keywords: List of search keywords
            original_query: Original user query
            
        Returns:
            Dictionary with API results and search parameters
        """
        # If no location extracted, try to use a default or query
        if not location:
            location = "United States"  # Default fallback
            self.logger.warning(f"No location provided, using fallback: '{location}'")
        
        # Construct query string from keywords
        query_string = " ".join(keywords) if keywords else original_query
        
        # Build query parameters
        querystring = {
            "location": location,
            "query": query_string
        }
        
        self.logger.info(f"Searching Yelp API - Location: '{location}', Query: '{query_string}'")
        
        try:
            # Execute API request
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=querystring
            )
            
            self.logger.debug(f"API response status: {response.status_code}")
            
            # Parse JSON response
            results = response.json()
            
            result_count = results.get('resultCount', 0)
            self.logger.info(f"Successfully retrieved {result_count} businesses")
            
            return {
                "results": results,
                "search_params": {
                    "location": location,
                    "query": query_string,
                    "original_query": original_query
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error during Yelp API search: {str(e)}")
            return {
                "results": {"error": str(e), "resultCount": 0, "results": []},
                "search_params": {
                    "location": location,
                    "query": query_string,
                    "original_query": original_query
                }
            }
