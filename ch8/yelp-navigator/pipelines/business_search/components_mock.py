"""
Mock version of components for testing without valid Yelp API key.
This allows you to test the LangGraph workflow while waiting for API access.
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
class YelpBusinessSearchMock:
    """
    Mock version of YelpBusinessSearch that returns sample data.
    Use this for testing the workflow without a valid API key.
    """
    
    def __init__(self, api_key: str = "mock"):
        """Initialize with mock data."""
        self.api_key = api_key
        self.logger = logging.getLogger(__name__ + ".YelpBusinessSearchMock")
    
    @component.output_types(
        results=Dict,
        search_params=Dict
    )
    def run(self, location: str, keywords: List[str], original_query: str) -> Dict[str, Any]:
        """
        Return mock Yelp business search results.
        
        Args:
            location: Location to search in
            keywords: List of search keywords
            original_query: Original user query
            
        Returns:
            Dictionary with mock API results and search parameters
        """
        if not location:
            location = "United States"
        
        query_string = " ".join(keywords) if keywords else original_query
        
        self.logger.info(f"🎭 MOCK MODE: Simulating Yelp search - Location: '{location}', Query: '{query_string}'")
        
        # Generate mock results based on the query
        mock_businesses = [
            {
                "alias": "tacodeli-austin",
                "name": "Tacodeli",
                "image_url": "https://s3-media1.fl.yelpcdn.com/bphoto/mock1.jpg",
                "is_closed": False,
                "url": "https://www.yelp.com/biz/tacodeli-austin",
                "review_count": 1234,
                "categories": [
                    {"alias": "mexican", "title": "Mexican"},
                    {"alias": "breakfast_brunch", "title": "Breakfast & Brunch"}
                ],
                "rating": 4.5,
                "coordinates": {"latitude": 30.2672, "longitude": -97.7431},
                "transactions": ["pickup", "delivery"],
                "price": "$$",
                "location": {
                    "address1": "1500 Spyglass Dr",
                    "city": location,
                    "zip_code": "78746",
                    "country": "US",
                    "state": "TX",
                    "display_address": ["1500 Spyglass Dr", f"{location}, TX 78746"]
                },
                "phone": "+15123427222",
                "display_phone": "(512) 342-7222"
            },
            {
                "alias": "veracruz-all-natural-austin",
                "name": "Veracruz All Natural",
                "image_url": "https://s3-media2.fl.yelpcdn.com/bphoto/mock2.jpg",
                "is_closed": False,
                "url": "https://www.yelp.com/biz/veracruz-all-natural-austin",
                "review_count": 2156,
                "categories": [
                    {"alias": "mexican", "title": "Mexican"},
                    {"alias": "breakfast_brunch", "title": "Breakfast & Brunch"}
                ],
                "rating": 4.7,
                "coordinates": {"latitude": 30.2642, "longitude": -97.7431},
                "transactions": ["pickup", "delivery"],
                "price": "$",
                "location": {
                    "address1": "1108 E 6th St",
                    "city": location,
                    "zip_code": "78702",
                    "country": "US",
                    "state": "TX",
                    "display_address": ["1108 E 6th St", f"{location}, TX 78702"]
                },
                "phone": "+15124743825",
                "display_phone": "(512) 474-3825"
            },
            {
                "alias": "suerte-austin",
                "name": "Suerte",
                "image_url": "https://s3-media3.fl.yelpcdn.com/bphoto/mock3.jpg",
                "is_closed": False,
                "url": "https://www.yelp.com/biz/suerte-austin",
                "review_count": 1876,
                "categories": [
                    {"alias": "mexican", "title": "Mexican"},
                    {"alias": "cocktailbars", "title": "Cocktail Bars"}
                ],
                "rating": 4.6,
                "coordinates": {"latitude": 30.2652, "longitude": -97.7311},
                "transactions": ["pickup", "delivery"],
                "price": "$$",
                "location": {
                    "address1": "1800 E 6th St",
                    "city": location,
                    "zip_code": "78702",
                    "country": "US",
                    "state": "TX",
                    "display_address": ["1800 E 6th St", f"{location}, TX 78702"]
                },
                "phone": "+15129156500",
                "display_phone": "(512) 915-6500"
            },
            {
                "alias": "el-naranjo-austin",
                "name": "El Naranjo",
                "image_url": "https://s3-media4.fl.yelpcdn.com/bphoto/mock4.jpg",
                "is_closed": False,
                "url": "https://www.yelp.com/biz/el-naranjo-austin",
                "review_count": 987,
                "categories": [
                    {"alias": "mexican", "title": "Mexican"},
                    {"alias": "oaxacan", "title": "Oaxacan"}
                ],
                "rating": 4.5,
                "coordinates": {"latitude": 30.2588, "longitude": -97.7445},
                "transactions": ["pickup", "delivery"],
                "price": "$$",
                "location": {
                    "address1": "85 Rainey St",
                    "city": location,
                    "zip_code": "78701",
                    "country": "US",
                    "state": "TX",
                    "display_address": ["85 Rainey St", f"{location}, TX 78701"]
                },
                "phone": "+15128148973",
                "display_phone": "(512) 814-8973"
            },
            {
                "alias": "la-condesa-austin",
                "name": "La Condesa",
                "image_url": "https://s3-media5.fl.yelpcdn.com/bphoto/mock5.jpg",
                "is_closed": False,
                "url": "https://www.yelp.com/biz/la-condesa-austin",
                "review_count": 1543,
                "categories": [
                    {"alias": "mexican", "title": "Mexican"},
                    {"alias": "cocktailbars", "title": "Cocktail Bars"}
                ],
                "rating": 4.4,
                "coordinates": {"latitude": 30.2676, "longitude": -97.7429},
                "transactions": ["pickup", "delivery"],
                "price": "$$",
                "location": {
                    "address1": "400 W 2nd St",
                    "city": location,
                    "zip_code": "78701",
                    "country": "US",
                    "state": "TX",
                    "display_address": ["400 W 2nd St", f"{location}, TX 78701"]
                },
                "phone": "+15124993900",
                "display_phone": "(512) 499-3900"
            }
        ]
        
        mock_results = {
            "resultCount": len(mock_businesses),
            "results": mock_businesses
        }
        
        self.logger.info(f"✅ MOCK MODE: Returning {len(mock_businesses)} mock businesses")
        
        return {
            "results": mock_results,
            "search_params": {
                "location": location,
                "query": query_string,
                "original_query": original_query
            }
        }
