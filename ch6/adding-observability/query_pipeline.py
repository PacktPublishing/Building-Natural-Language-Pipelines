import wandb
from haystack import Pipeline
from haystack.components.embedders import OpenAITextEmbedder
from haystack_integrations.components.retrievers.elasticsearch import ElasticsearchEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack.utils import Secret
from dotenv import load_dotenv
import os
import time

# Initialize Weights and Biases
wandb.init(project="haystack-querying", config={"task": "Querying Pipeline"})

load_dotenv(".env")
open_ai_key = os.environ.get("OPENAI_API_KEY")

# Initialize components
document_store = ElasticsearchDocumentStore(hosts="http://localhost:9200")
text_embedder = OpenAITextEmbedder(api_key=Secret.from_token(open_ai_key))
retriever = ElasticsearchEmbeddingRetriever(document_store=document_store)
generator = OpenAIGenerator(model="gpt-4o-mini", api_key=open_ai_key)

# Define template
template = """
Given the following information, answer the question.
Context:
{% for document in documents %}
{{ document.content }}
{% endfor %}
Question: {{question}}
Answer:
"""
prompt_builder = PromptBuilder(template=template)

# Build and connect components in the pipeline
query_pipeline = Pipeline()
query_pipeline.add_component("text_embedder", text_embedder)
query_pipeline.add_component("retriever", retriever)
query_pipeline.add_component("prompt_builder", prompt_builder)
query_pipeline.add_component("generator", generator)
query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
query_pipeline.connect("retriever", "prompt_builder.documents")
query_pipeline.connect("prompt_builder", "generator")

# Run a query through the pipeline
def query_pipeline_run(question):
    start_time = time.time()
    
    # Embed question
    embedding_start = time.time()
    question_embedding = text_embedder.embed({"text": question})
    embedding_end = time.time()
    
    # Retrieve documents and measure retrieval time
    retrieval_start = time.time()
    retrieved_docs = retriever.retrieve(question_embedding)
    retrieval_end = time.time()
    
    # Generate response and log metrics
    prompt = prompt_builder.build({"documents": retrieved_docs, "question": question})
    generation_start = time.time()
    response = generator.generate({"prompt": prompt})
    generation_end = time.time()
    
    # Log query pipeline metrics to Weights and Biases
    wandb.log({
        "question_length": len(question),
        "embedding_time": embedding_end - embedding_start,
        "retrieval_time": retrieval_end - retrieval_start,
        "generation_time": generation_end - generation_start,
        "retrieved_documents_count": len(retrieved_docs),
        "response_accuracy": "placeholder_accuracy_metric"  # Replace with your accuracy measurement if available
    })
    
    return response

# Test with a question
question = "Tell me about the latest news in the dataset."
response = query_pipeline_run(question)
print(response["replies"][0])

wandb.finish()
