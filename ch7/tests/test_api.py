#!/usr/bin/env python3
"""
Test script for the Hybrid RAG FastAPI application.
Run this after starting the services to test the API endpoints.
"""

import requests
import json
import time
import sys
from typing import Optional

# API base URL
BASE_URL = "http://localhost:8000"


def test_connection():
    """Test basic connection to the API."""
    print("🔗 Testing connection...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Connection successful: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_health_endpoint():
    """Test the health check endpoint."""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Health: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200 and data.get("status") == "healthy":
            print("✅ Health check passed")
            return True
        else:
            print("⚠️  Health check indicates issues")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_info_endpoint():
    """Test the info endpoint."""
    print("ℹ️  Testing info endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/info", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Info: {json.dumps(data, indent=2)}")
            print("✅ Info endpoint working")
            return True
        else:
            print(f"❌ Info endpoint failed: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Info endpoint error: {e}")
        return False


def test_query_endpoint():
    """Test the query endpoint with a sample question."""
    print("❓ Testing query endpoint...")
    try:
        query_data = {
            "query": "What is retrieval augmented generation?",
            "top_k": 3
        }
        
        print(f"Sending query: {query_data['query']}")
        response = requests.post(
            f"{BASE_URL}/query", 
            json=query_data,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Answer: {data.get('answer', 'No answer')[:200]}...")
            print(f"Documents retrieved: {len(data.get('documents', []))}")
            print("✅ Query endpoint working")
            return True
        else:
            print(f"❌ Query failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Query error: {e}")
        return False




def wait_for_api(max_retries: int = 30, delay: int = 2):
    """Wait for the API to be available."""
    print(f"⏳ Waiting for API to be available (max {max_retries * delay}s)...")
    
    for attempt in range(max_retries):
        if test_connection():
            print("✅ API is available")
            return True
        print(f"Attempt {attempt + 1}/{max_retries}...")
        time.sleep(delay)
    
    print("❌ API not available after waiting")
    return False


def run_comprehensive_test():
    """Run all tests in sequence."""
    print("🚀 Starting comprehensive API tests...\n")
    
    # Wait for API
    if not wait_for_api():
        print("❌ Cannot proceed - API not available")
        return False
    
    print()
    
    # Run all tests
    tests = [
        ("Connection", test_connection),
        ("Health Check", test_health_endpoint),
        ("Info Endpoint", test_info_endpoint),
        ("Query Endpoint", test_query_endpoint),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            results.append((name, False))
        
        time.sleep(1)  # Small delay between tests
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed - check the API and Elasticsearch")
        return False


def main():
    """Main function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "wait":
            wait_for_api()
        elif sys.argv[1] == "health":
            test_health_endpoint()
        elif sys.argv[1] == "query":
            test_query_endpoint()
        else:
            print("Usage: python test_api.py [wait|health|query]")
    else:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()