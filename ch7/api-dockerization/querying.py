
from haystack import Pipeline
from haystack.components.embedders import OpenAITextEmbedder 
from haystack.utils import Secret
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator

from dotenv import load_dotenv
import os
import wandb
import time

load_dotenv(".env")
open_ai_key = os.environ.get("OPENAI_API_KEY")

class RetrieveDocuments:
    
    def __init__(self, doc_store, open_ai_key):
        
        # Initialize a text embedder to create an embedding for the user query.
        text_embedder = OpenAITextEmbedder(api_key=Secret.from_token(open_ai_key))

        # Initialize retriever
        retriever = InMemoryEmbeddingRetriever(document_store=doc_store)

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
        self.query_pipeline = Pipeline()
        self.query_pipeline.add_component("text_embedder", text_embedder)
        self.query_pipeline.add_component("retriever", retriever)
        self.query_pipeline.add_component("prompt_builder", prompt_builder)
        self.query_pipeline.add_component("llm", generator)
        self.query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        self.query_pipeline.connect("retriever", "prompt_builder.documents")
        self.query_pipeline.connect("prompt_builder", "llm")
        
    def run(self, query):
        return self.query_pipeline.run(query)


# query_pipeline = RetrieveDocuments()


# # Running the pipeline
# question = "Tell me about what you know"
# start_time = time.time()
# response = query_pipeline.run({"text_embedder": {"text": question}, "prompt_builder": {"question": question}})
# end_time = time.time()

        
# print(response["llm"]["replies"][0])
