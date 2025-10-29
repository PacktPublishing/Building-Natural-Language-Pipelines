# Import necessary components for the query pipeline
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret
from haystack import Pipeline, SuperComponent
from scripts.indexing import document_store

# Text Embedder: To embed the user's query. Must be compatible with the document embedder.
text_embedder = SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")

# Retriever: Fetches documents from the DocumentStore based on vector similarity.
retriever = InMemoryEmbeddingRetriever(document_store=document_store, top_k=3)

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



naive_rag_pipeline = Pipeline()

# Add components to the pipeline
naive_rag_pipeline.add_component("text_embedder", text_embedder)
naive_rag_pipeline.add_component("retriever", retriever)
naive_rag_pipeline.add_component("prompt_builder", prompt_builder_inst)
naive_rag_pipeline.add_component("llm", llm_generator_inst)

# --- 3. Connect the Components ---

# The query embedding is sent to the retriever
naive_rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
# The retriever's documents are sent to the prompt builder
naive_rag_pipeline.connect("retriever.documents", "prompt_builder.documents")
# The final prompt is sent to the LLM
naive_rag_pipeline.connect("prompt_builder.prompt", "llm.prompt")

# --- 4. Create SuperComponent for Easy Integration ---

naive_rag_sc = SuperComponent(
    pipeline=naive_rag_pipeline,
    input_mapping={
        "query": ["text_embedder.text", 

                  "prompt_builder.question"],
    },
    output_mapping={
        "llm.replies": "replies",

    }
)