# Import additional components for hybrid retrieval
from haystack_integrations.components.retrievers.elasticsearch import ElasticsearchBM25Retriever, ElasticsearchEmbeddingRetriever
from haystack.components.joiners import DocumentJoiner
from haystack.components.rankers import SentenceTransformersSimilarityRanker

# Import necessary components for the query pipeline
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret
from haystack import Pipeline, SuperComponent

from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore

document_store = ElasticsearchDocumentStore(hosts="http://localhost:9200")

# --- 1. Initialize Query Pipeline Components ---

# Text Embedder: To embed the user's query. Must be compatible with the document embedder.
text_embedder = SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")

# Retriever: Fetches documents from the Elasticsearch DocumentStore based on vector similarity.
retriever = ElasticsearchEmbeddingRetriever(document_store=document_store, top_k=3)

# PromptBuilder: Creates a prompt using the retrieved documents and the query.
# The Jinja2 template iterates through the documents and adds their content to the prompt.
prompt_template_for_pipeline = """
Given the following information, answer the user's question.
If the information is not available in the provided documents, say that you don't have enough information to answer.

Context:
{% for doc in documents %}
    {{ doc.content }}
{% endfor %}

Question: {{question}}
Answer:
"""
prompt_builder_inst = PromptBuilder(template=prompt_template_for_pipeline,
                                    required_variables="*")
llm_generator_inst = OpenAIGenerator(api_key=Secret.from_env_var("OPENAI_API_KEY"), model="gpt-4o-mini")



# Sparse Retriever (BM25): For keyword-based search using Elasticsearch.
# Elasticsearch provides built-in BM25 scoring for text-based retrieval.
bm25_retriever = ElasticsearchBM25Retriever(document_store=document_store, top_k=3)

# DocumentJoiner: To merge the results from the two retrievers.
# The default 'concatenate' mode works well here as the ranker will handle final ordering.
document_joiner = DocumentJoiner()

# Ranker: A cross-encoder model to re-rank the combined results for higher precision.
# This model is highly effective at identifying the most relevant documents from a candidate set.
ranker = SentenceTransformersSimilarityRanker(model="BAAI/bge-reranker-base", top_k=3)

# --- 2. Build the Hybrid RAG Pipeline ---

hybrid_rag_pipeline = Pipeline()

# Add all necessary components
hybrid_rag_pipeline.add_component("text_embedder", text_embedder)
hybrid_rag_pipeline.add_component("embedding_retriever", retriever) # Dense retriever
hybrid_rag_pipeline.add_component("bm25_retriever", bm25_retriever) # Sparse retriever
hybrid_rag_pipeline.add_component("document_joiner", document_joiner)
hybrid_rag_pipeline.add_component("ranker", ranker)
hybrid_rag_pipeline.add_component("prompt_builder", prompt_builder_inst)
hybrid_rag_pipeline.add_component("llm", llm_generator_inst)

# --- 3. Connect the Components in a Graph ---

# The query is embedded for the dense retriever
hybrid_rag_pipeline.connect("text_embedder.embedding", "embedding_retriever.query_embedding")

# The raw query text is sent to the BM25 retriever and the ranker
# Note: The query input for these components is the raw text string.

# The outputs of both retrievers are fed into the document joiner
hybrid_rag_pipeline.connect("embedding_retriever.documents", "document_joiner.documents")
hybrid_rag_pipeline.connect("bm25_retriever.documents", "document_joiner.documents")

# The joined documents are sent to the ranker
hybrid_rag_pipeline.connect("document_joiner.documents", "ranker.documents")

# The ranked documents are sent to the prompt builder
hybrid_rag_pipeline.connect("ranker.documents", "prompt_builder.documents")

# The final prompt is sent to the LLM
hybrid_rag_pipeline.connect("prompt_builder.prompt", "llm.prompt")

# --- 4. Wrap the Pipeline in a SuperComponent ---
hybrid_rag_sc = SuperComponent(
    pipeline=hybrid_rag_pipeline,
    input_mapping={
        "query": ["text_embedder.text", 
                  "bm25_retriever.query",
                  "ranker.query",
                  "prompt_builder.question"],
    },
    output_mapping={
        "llm.replies": "replies",
        "ranker.documents": "documents"
    }
)