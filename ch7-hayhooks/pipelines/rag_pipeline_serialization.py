from haystack import Pipeline
from haystack.components.embedders import OpenAITextEmbedder
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.components.joiners import DocumentJoiner
from haystack.components.rankers import SentenceTransformersSimilarityRanker
from haystack.utils import Secret
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantSparseEmbeddingRetriever, QdrantEmbeddingRetriever
from haystack_integrations.components.embedders.fastembed import FastembedSparseTextEmbedder
import os
from dotenv import load_dotenv
load_dotenv()

# Initialize document store (same path as indexing)
document_store = QdrantDocumentStore(
    path="./qdrant_storage",
    index="documents",
    embedding_dim=1536,  # text-embedding-3-small dimension
    recreate_index=False,
    use_sparse_embeddings=True  # Enable sparse embeddings for BM25-like retrieval
)

        
pipeline = Pipeline()
        
# Core components
text_embedder = OpenAITextEmbedder(
    api_key=Secret.from_env_var("OPENAI_API_KEY"),
    model="text-embedding-3-small"
)

# Add sparse embedder for BM25 retriever (using FastEmbed)
sparse_text_embedder = FastembedSparseTextEmbedder()

embedding_retriever = QdrantEmbeddingRetriever(
    document_store=document_store,
    top_k=3
)

bm25_retriever = QdrantSparseEmbeddingRetriever(
    document_store=document_store,
    top_k=3
)

document_joiner = DocumentJoiner()

ranker = SentenceTransformersSimilarityRanker(
    model="BAAI/bge-reranker-base",
    top_k=3
)

prompt_template = """
Given the following information, answer the user's question.
If the information is not available in the provided documents, say that you don't have enough information to answer.

Context:
{% for doc in documents %}
    {{ doc.content }}
{% endfor %}

Question: {{question}}
Answer:
"""

prompt_builder = PromptBuilder(
    template=prompt_template,
    required_variables=["documents", "question"]
)

llm = OpenAIGenerator(
    api_key=Secret.from_env_var("OPENAI_API_KEY"),
    model="gpt-4o-mini"
)

# Add components
pipeline.add_component("text_embedder", text_embedder)
pipeline.add_component("sparse_text_embedder", sparse_text_embedder)
pipeline.add_component("embedding_retriever", embedding_retriever)
pipeline.add_component("bm25_retriever", bm25_retriever)
pipeline.add_component("document_joiner", document_joiner)
pipeline.add_component("ranker", ranker)
pipeline.add_component("prompt_builder", prompt_builder)
pipeline.add_component("llm", llm)

# Connect components
pipeline.connect("text_embedder.embedding", "embedding_retriever.query_embedding")
pipeline.connect("sparse_text_embedder.sparse_embedding", "bm25_retriever.query_sparse_embedding")
pipeline.connect("embedding_retriever.documents", "document_joiner.documents")
pipeline.connect("bm25_retriever.documents", "document_joiner.documents")
pipeline.connect("document_joiner.documents", "ranker.documents")
pipeline.connect("ranker.documents", "prompt_builder.documents")
pipeline.connect("prompt_builder.prompt", "llm.prompt")

output_path = "./pipelines/hybrid_rag/rag.yml"
# Dump the pipeline
with open(output_path, "w") as file:
  pipeline.dump(file)
  
print(f"Pipeline serialized to {output_path}")