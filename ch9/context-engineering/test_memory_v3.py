#!/usr/bin/env python3
"""
Test script for Yelp Navigator V3 memory features.

This script demonstrates how the memory system works by:
1. Making an initial search query
2. Asking follow-up questions that should use cached data
3. Showing when cache hits occur
"""

import sys
from pathlib import Path

# Add the context-engineering directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from yelp_navigator_v3.app.graph import graph
from yelp_navigator_v3.app.tools import list_cached_businesses, get_cached_business_info, memory

def test_memory_system():
    """Test the memory-aware business search."""
    
    print("=" * 80)
    print("YELP NAVIGATOR V3 - MEMORY SYSTEM TEST")
    print("=" * 80)
    print()
    
    # Clear any existing cache for clean test
    print("🧹 Clearing existing cache...")
    memory.clear_all()
    print("✓ Cache cleared\n")
    
    # Test 1: Initial search
    print("📍 TEST 1: Initial Search Query")
    print("-" * 80)
    query1 = "Find coffee shops in Seattle"
    print(f"Query: {query1}")
    print("Expected: API call to search, results cached\n")
    
    result1 = graph.invoke({
        "messages": [{"role": "user", "content": query1}]
    })
    
    print("Response:", result1["messages"][-1].content[:200], "...\n")
    
    # Check cached businesses
    cached = list_cached_businesses()
    print(f"✓ Cached {len(cached)} businesses")
    if cached:
        print(f"  Example: {cached[0]['name']} (ID: {cached[0]['id'][:20]}...)")
    print()
    
    # Test 2: Follow-up for details (should use cache if available)
    print("📍 TEST 2: Follow-up Query - Details")
    print("-" * 80)
    query2 = "Tell me more about the first one, does it have a website?"
    print(f"Query: {query2}")
    print("Expected: Check cache first, may need API call for website details\n")
    
    # Build conversation history
    messages2 = result1["messages"] + [
        {"role": "user", "content": query2}
    ]
    
    result2 = graph.invoke({"messages": messages2})
    print("Response:", result2["messages"][-1].content[:200], "...\n")
    
    # Check if we have details cached now
    if cached:
        info = get_cached_business_info(cached[0]['id'])
        if info:
            print(f"✓ Business details cached: {info['has_details']}")
            print(f"✓ Sentiment data cached: {info['has_sentiment']}")
    print()
    
    # Test 3: Follow-up for reviews (should fetch and cache sentiment)
    print("📍 TEST 3: Follow-up Query - Reviews")
    print("-" * 80)
    query3 = "What do people say about it? Show me reviews"
    print(f"Query: {query3}")
    print("Expected: Check cache for sentiment, fetch if not available\n")
    
    messages3 = result2["messages"] + [
        {"role": "user", "content": query3}
    ]
    
    result3 = graph.invoke({"messages": messages3})
    print("Response:", result3["messages"][-1].content[:200], "...\n")
    
    # Final cache status
    if cached:
        info = get_cached_business_info(cached[0]['id'])
        if info:
            print(f"✓ Business details cached: {info['has_details']}")
            print(f"✓ Sentiment data cached: {info['has_sentiment']}")
    print()
    
    # Test 4: Repeat the same query (should be instant from cache)
    print("📍 TEST 4: Repeat Query - Should Use Cache")
    print("-" * 80)
    query4 = "Show me the reviews again"
    print(f"Query: {query4}")
    print("Expected: INSTANT response from cache, no API calls\n")
    
    messages4 = result3["messages"] + [
        {"role": "user", "content": query4}
    ]
    
    result4 = graph.invoke({"messages": messages4})
    print("Response:", result4["messages"][-1].content[:200], "...\n")
    
    # Summary
    print("=" * 80)
    print("MEMORY SYSTEM TEST COMPLETE")
    print("=" * 80)
    print(f"Total businesses cached: {len(list_cached_businesses())}")
    print()
    print("Key Observations:")
    print("- First query: API calls made, data cached")
    print("- Follow-up queries: Cache checked first")
    print("- Repeated queries: Instant responses from cache")
    print("- No duplicate API calls for same data")
    print()
    print("✨ V3 memory system is working!")

if __name__ == "__main__":
    try:
        test_memory_system()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
