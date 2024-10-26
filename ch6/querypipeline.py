from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack import Pipeline
from haystack.components.embedders import OpenAITextEmbedder 
from haystack.utils import Secret
from haystack_integrations.components.retrievers.elasticsearch import ElasticsearchEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator

from dotenv import load_dotenv
import os 

load_dotenv(".env")
open_ai_key = os.environ.get("OPENAI_API_KEY")

from haystack.components.embedders import SentenceTransformersTextEmbedder


# Initialize ElasticsearchDocumentStore
document_store = ElasticsearchDocumentStore(hosts = "http://localhost:9200")

# Initialize a text embedder to create an embedding for the user query.
text_embedder = OpenAITextEmbedder(api_key=Secret.from_token(open_ai_key))

# Initialize retriever
retriever = ElasticsearchEmbeddingRetriever(document_store=document_store)

# Define the template prompt
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

# Initialize Generator (Replace 'your-api-key' with your OpenAI API Key)
generator = OpenAIGenerator(model="gpt-4o-mini")
generator.api_key = open_ai_key

# Build the Pipeline
query_pipeline = Pipeline()
query_pipeline.add_component("text_embedder", text_embedder)
query_pipeline.add_component("retriever", retriever)
query_pipeline.add_component("prompt_builder", prompt_builder)
query_pipeline.add_component("llm", generator)
query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
query_pipeline.connect("retriever", "prompt_builder.documents")
query_pipeline.connect("prompt_builder", "llm")

# Running the pipeline
question = "Tell me about what you know"
response = query_pipeline.run({"text_embedder": {"text": question}, "prompt_builder": {"question": question}})
print(response["llm"]["replies"][0])
