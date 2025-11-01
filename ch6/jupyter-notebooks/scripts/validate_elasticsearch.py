#!/usr/bin/env python3
"""
Simple validation script to check Elasticsearch integration without running full pipelines
"""
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack_integrations.components.retrievers.elasticsearch import ElasticsearchEmbeddingRetriever
from haystack.components.embedders import SentenceTransformersTextEmbedder

def test_elasticsearch_connection():
    """Test basic Elasticsearch connectivity and document retrieval"""
    try:
        # Initialize document store
        document_store = ElasticsearchDocumentStore(hosts="http://localhost:9200")
        
        # Test document count
        count = document_store.count_documents()
        print(f"✅ Connected to Elasticsearch successfully!")
        print(f"📊 Total documents in index: {count}")
        
        # Test retriever initialization
        retriever = ElasticsearchEmbeddingRetriever(document_store=document_store, top_k=3)
        print(f"✅ ElasticsearchEmbeddingRetriever initialized successfully!")
        
        # Test basic retrieval with embedder
        embedder = SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
        embedder.warm_up()
        
        # Generate embedding for test query
        query = "Haystack framework"
        embedding_result = embedder.run(text=query)
        query_embedding = embedding_result["embedding"]
        
        # Retrieve documents
        results = retriever.run(query_embedding=query_embedding)
        docs = results["documents"]
        print(f"✅ Retrieved {len(docs)} documents for test query '{query}'")
        
        # Show first document snippet
        if docs:
            print(f"📄 First document snippet: {docs[0].content[:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_elasticsearch_connection()
    if success:
        print("\n🎉 All Elasticsearch components are working correctly!")
        print("✅ Both naive and hybrid RAG pipelines should work with the indexed documents.")
    else:
        print("\n❌ There are issues with the Elasticsearch setup.")