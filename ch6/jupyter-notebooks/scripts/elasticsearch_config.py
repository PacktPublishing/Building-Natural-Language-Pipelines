"""
Elasticsearch Configuration Helper
Provides connection details and helper functions for dual Elasticsearch setup.
"""

from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from typing import Dict, Any


class ElasticsearchConfig:
    """Configuration class for dual Elasticsearch instances."""
    
    # Connection URLs
    SMALL_ES_URL = "http://localhost:9200"
    LARGE_ES_URL = "http://localhost:9201"
    
    # Default index names for different embedding types
    SMALL_EMBEDDING_INDEX = "small_embeddings"
    LARGE_EMBEDDING_INDEX = "large_embeddings"
    
    # Instance configurations
    SMALL_CONFIG = {
        "hosts": SMALL_ES_URL,
        "timeout": 30,
        "max_retries": 3,
        "retry_on_timeout": True
    }
    
    LARGE_CONFIG = {
        "hosts": LARGE_ES_URL, 
        "timeout": 60,
        "max_retries": 5,
        "retry_on_timeout": True
    }

    @classmethod
    def get_small_document_store(cls, index_name: str = None) -> ElasticsearchDocumentStore:
        """
        Get document store for small embeddings instance.
        
        Args:
            index_name: Optional index name, defaults to SMALL_EMBEDDING_INDEX
            
        Returns:
            ElasticsearchDocumentStore configured for small instance
        """
        index_name = index_name or cls.SMALL_EMBEDDING_INDEX
        return ElasticsearchDocumentStore(
            hosts=cls.SMALL_ES_URL,
            index=index_name
        )
    
    @classmethod
    def get_large_document_store(cls, index_name: str = None) -> ElasticsearchDocumentStore:
        """
        Get document store for large embeddings instance.
        
        Args:
            index_name: Optional index name, defaults to LARGE_EMBEDDING_INDEX
            
        Returns:
            ElasticsearchDocumentStore configured for large instance
        """
        index_name = index_name or cls.LARGE_EMBEDDING_INDEX
        return ElasticsearchDocumentStore(
            hosts=cls.LARGE_ES_URL,
            index=index_name
        )
    
    @classmethod
    def get_dual_document_store(cls, instance_type: str = "large", index_name: str = None) -> ElasticsearchDocumentStore:
        """
        Get document store for dual embeddings (both small and large in same docs).
        
        Args:
            instance_type: "small" or "large" - which instance to use for storage
            index_name: Optional index name, defaults to DUAL_EMBEDDING_INDEX
            
        Returns:
            ElasticsearchDocumentStore configured for dual embeddings
        """
        index_name = index_name
        
        if instance_type == "small":
            return ElasticsearchDocumentStore(
                hosts=cls.SMALL_ES_URL,
                index=index_name
            )
        else:
            return ElasticsearchDocumentStore(
                hosts=cls.LARGE_ES_URL,
                index=index_name
            )
    
    @classmethod
    def test_connections(cls) -> Dict[str, bool]:
        """
        Test connections to both Elasticsearch instances.
        
        Returns:
            Dict with connection status for each instance
        """
        results = {}
        
        try:
            small_store = cls.get_small_document_store("test_small")
            # Test by attempting to get document count
            small_store.count_documents()
            results["small_instance"] = True
        except Exception as e:
            print(f"Small instance connection failed: {e}")
            results["small_instance"] = False
        
        try:
            large_store = cls.get_large_document_store("test_large")
            # Test by attempting to get document count
            large_store.count_documents()
            results["large_instance"] = True
        except Exception as e:
            print(f"Large instance connection failed: {e}")
            results["large_instance"] = False
            
        return results


# Usage examples and constants
EMBEDDING_STRATEGIES = {
    "small_only": {
        "description": "Use only small embeddings for fast retrieval",
        "instance": "small",
        "models": ["text-embedding-3-small"]
    },
    "large_only": {
        "description": "Use only large embeddings for high accuracy",
        "instance": "large", 
        "models": ["text-embedding-3-large"]
    },
    "separate_instances": {
        "description": "Store small and large embeddings in separate instances",
        "instance": "both",
        "models": ["text-embedding-3-small", "text-embedding-3-large"]
    }
}


if __name__ == "__main__":
    print("Testing Elasticsearch connections...")
    config = ElasticsearchConfig()
    
    # Test connections
    results = config.test_connections()
    print(f"Connection results: {results}")
    
    # Print configuration details
    print(f"\nSmall instance URL: {config.SMALL_ES_URL}")
    print(f"Large instance URL: {config.LARGE_ES_URL}")
    
    print(f"\nDefault indices:")
    print(f"Small embeddings: {config.SMALL_EMBEDDING_INDEX}")
    print(f"Large embeddings: {config.LARGE_EMBEDDING_INDEX}")