#!/usr/bin/env python3
"""
Test script to verify multi-location query handling.
Tests the fix for queries like "best coffee places, best cheese in Vancouver, LA"
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:1416"

def test_query(query: str, description: str):
    """Test a query and display results."""
    print("\n" + "="*80)
    print(f"TEST: {description}")
    print("="*80)
    print(f"Query: {query}\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/business_search/run",
            json={"query": query},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            
            print(f"✅ SUCCESS")
            print(f"Status Code: {response.status_code}\n")
            
            # Display extraction results
            print("--- EXTRACTION RESULTS ---")
            print(f"Extracted Locations: {result.get('extracted_locations', [])}")
            print(f"Extracted Keywords: {result.get('extracted_keywords', [])}")
            print(f"Is Multi-Query: {result.get('is_multi_query', False)}")
            print(f"Total Searches: {result.get('total_searches', 1)}\n")
            
            # Display search parameters
            search_params = result.get('search_params', {})
            searches = search_params.get('searches', [])
            print(f"--- SEARCH PARAMETERS ({len(searches)} searches) ---")
            for i, search in enumerate(searches, 1):
                print(f"{i}. Location: {search.get('location')}")
                print(f"   Query: {search.get('query')}")
                print(f"   Results: {search.get('result_count', 0)}\n")
            
            # Display business results summary
            businesses = result.get('businesses', [])
            print(f"--- BUSINESS RESULTS ({len(businesses)} total) ---")
            for i, biz in enumerate(businesses[:5], 1):  # Show first 5
                print(f"{i}. {biz.get('name')}")
                print(f"   Categories: {', '.join(biz.get('categories', []))}")
                print(f"   Rating: {biz.get('rating')} ({biz.get('review_count')} reviews)")
                location = biz.get('location', {})
                print(f"   Location: ({location.get('lat')}, {location.get('lon')})\n")
            
            if len(businesses) > 5:
                print(f"   ... and {len(businesses) - 5} more businesses")
            
        else:
            print(f"❌ FAILED")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def main():
    """Run all test cases."""
    print("\n" + "🧪 MULTI-LOCATION QUERY TESTS " + "🧪")
    print("Testing enhanced query parsing and multi-location handling\n")
    
    # Test 1: Original problematic query
    test_query(
        "best coffee places, best cheese in Vancouver, LA",
        "Comma-separated items with multiple locations (original issue)"
    )
    
    # Test 2: Multiple locations with single item
    test_query(
        "coffee shops in Vancouver, LA",
        "Single item with multiple locations"
    )
    
    # Test 3: Traditional "and" separator
    test_query(
        "coffee in Vancouver and pizza in LA",
        "Traditional ' and ' separator (should still work)"
    )
    
    # Test 4: Single location control
    test_query(
        "best coffee and cheese in Vancouver",
        "Multiple items in single location (control test)"
    )
    
    print("\n" + "="*80)
    print("🎉 TESTS COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
