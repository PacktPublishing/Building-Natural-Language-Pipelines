"""
Elasticsearch Configuration Helper
Provides connection details and helper functions for dual Elasticsearch setup.
"""

from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from typing import Dict, Any, Optional
import requests


class ElasticsearchConfig:
    """Configuration class for dual Elasticsearch instances."""

    # Connection URLs
    SMALL_ES_URL = "http://localhost:9200"
    LARGE_ES_URL = "http://localhost:9201"

    # Default index names for different embedding types
    SMALL_EMBEDDING_INDEX = "small_embeddings"
    LARGE_EMBEDDING_INDEX = "large_embeddings"
    DUAL_EMBEDDING_INDEX = "dual_embeddings"

    @classmethod
    def get_small_document_store(cls, index_name: Optional[str] = None) -> ElasticsearchDocumentStore:
        """Get document store for small embeddings instance."""
        index_name = index_name or cls.SMALL_EMBEDDING_INDEX
        return ElasticsearchDocumentStore(hosts=cls.SMALL_ES_URL, index=index_name)

    @classmethod  
    def get_large_document_store(cls, index_name: Optional[str] = None) -> ElasticsearchDocumentStore:
        """Get document store for large embeddings instance."""
        index_name = index_name or cls.LARGE_EMBEDDING_INDEX
        return ElasticsearchDocumentStore(hosts=cls.LARGE_ES_URL, index=index_name)

    @classmethod
    def test_connections(cls) -> Dict[str, bool]:
        """Test connections to both Elasticsearch instances."""
        results = {}

        for name, url in [("small", cls.SMALL_ES_URL), ("large", cls.LARGE_ES_URL)]:
            try:
                response = requests.get(f"{url}/_cluster/health", timeout=10)
                results[f"{name}_instance"] = response.status_code == 200
            except Exception:
                results[f"{name}_instance"] = False

        return results

# Connection URLs for easy access
ES_CONNECTIONS = {
    "small": "http://localhost:9200",
    "large": "http://localhost:9201"
}
