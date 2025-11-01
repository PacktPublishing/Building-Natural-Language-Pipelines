#!/usr/bin/env python3
"""
Test script to verify that both naive and hybrid RAG pipelines work with Elasticsearch.
Run this after indexing.py has populated the Elasticsearch document store.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

def test_naive_rag():
    """Test the naive RAG pipeline"""
    print("=" * 50)
    print("Testing Naive RAG Pipeline")
    print("=" * 50)
    
    try:
        from naiverag import naive_rag_sc
        
        # Test query
        query = "What is Haystack and what are its main features?"
        
        print(f"Query: {query}")
        print("\nRunning naive RAG pipeline...")
        
        result = naive_rag_sc.run(query="What is Haystack and what are its main features?")
        
        print("\nResponse:")
        print(result["replies"][0])
        print("\n" + "="*50)
        return True
        
    except Exception as e:
        print(f"Error in naive RAG: {e}")
        return False

def test_hybrid_rag():
    """Test the hybrid RAG pipeline"""
    print("Testing Hybrid RAG Pipeline")
    print("=" * 50)
    
    try:
        from hybridrag import hybrid_rag_sc
        
        # Test query
        query = "How do people use ChatGPT according to the research?"
        
        print(f"Query: {query}")
        print("\nRunning hybrid RAG pipeline...")

        result = hybrid_rag_sc.run(query="How do people use ChatGPT according to the research?")

        print("\nResponse:")
        print(result["replies"][0])
        
        print(f"\nRetrieved {len(result['documents'])} documents")
        for i, doc in enumerate(result['documents'][:2]):  # Show first 2 docs
            print(f"\nDocument {i+1} preview: {doc.content[:200]}...")
        
        print("\n" + "="*50)
        return True
        
    except Exception as e:
        print(f"Error in hybrid RAG: {e}")
        return False

def main():
    """Run both tests"""
    print("Testing RAG Pipelines with Elasticsearch Document Store")
    print("Make sure Elasticsearch is running and documents are indexed!")
    print("\n")
    
    # Check if OPENAI_API_KEY is set
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in environment variables!")
        print("Please set it in your .env file")
        return
    
    success_count = 0
    
    # Test naive RAG
    if test_naive_rag():
        success_count += 1
    
    # Test hybrid RAG
    if test_hybrid_rag():
        success_count += 1
    
    print(f"\nSummary: {success_count}/2 tests passed")
    
    if success_count == 2:
        print("✅ Both RAG pipelines are working correctly with Elasticsearch!")
    else:
        print("❌ Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()