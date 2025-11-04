# Import necessary components for the query pipeline
from haystack.components.embedders import OpenAITextEmbedder
from haystack_integrations.components.retrievers.elasticsearch import ElasticsearchEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret
from haystack import Pipeline, super_component
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from typing import Optional
import os


@super_component
class NaiveRAGSuperComponent:
    def __init__(self, 
                 document_store, 
                 embedder_model: str = "text-embedding-3-small", 
                 llm_model: str = "gpt-4o-mini", 
                 top_k: int = 3,
                 openai_api_key: Optional[str] = None):
        """
        Initialize the Naive RAG SuperComponent.
        
        Args:
            document_store: Elasticsearch document store
            embedder_model (str): OpenAI embedding model name. Defaults to "text-embedding-3-small".
            llm_model (str): OpenAI LLM model name. Defaults to "gpt-4o-mini".
            top_k (int): Number of documents to retrieve. Defaults to 3.
            openai_api_key (Optional[str]): OpenAI API key. If None, will use environment variable.
        """
        self.embedder_model = embedder_model
        self.llm_model = llm_model
        self.top_k = top_k
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")
        
        self._build_pipeline(document_store)
    
    def _build_pipeline(self, document_store):
        """Build the naive RAG pipeline with initialized components."""
        
        # Text Embedder: To embed the user's query. Must be compatible with the document embedder.
        text_embedder = OpenAITextEmbedder(
            api_key=Secret.from_token(self.openai_api_key), 
            model=self.embedder_model
        )

        # Retriever: Fetches documents from the Elasticsearch DocumentStore based on vector similarity.
        retriever = ElasticsearchEmbeddingRetriever(document_store=document_store, top_k=self.top_k)

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
        llm_generator_inst = OpenAIGenerator(
            api_key=Secret.from_token(self.openai_api_key), 
            model=self.llm_model
        )

        # --- 2. Build the Pipeline ---
        self.pipeline = Pipeline()

        # Add components to the pipeline
        self.pipeline.add_component("text_embedder", text_embedder)
        self.pipeline.add_component("retriever", retriever)
        self.pipeline.add_component("prompt_builder", prompt_builder_inst)
        self.pipeline.add_component("llm", llm_generator_inst)

        # --- 3. Connect the Components ---

        # The query embedding is sent to the retriever
        self.pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        # The retriever's documents are sent to the prompt builder
        self.pipeline.connect("retriever.documents", "prompt_builder.documents")
        # The final prompt is sent to the LLM
        self.pipeline.connect("prompt_builder.prompt", "llm.prompt")

        # --- 4. Define Input and Output Mappings ---
        self.input_mapping = {
            "query": ["text_embedder.text", "prompt_builder.question"]
        }

        self.output_mapping = {
            "llm.replies": "replies",
            "retriever.documents": "documents"
        }


if __name__ == "__main__":
    # Initialize the document store
    from dotenv import load_dotenv
    load_dotenv(".env")
    document_store = ElasticsearchDocumentStore(hosts="http://localhost:9200")
    
    # Create the Naive RAG SuperComponent
    naive_rag_sc = NaiveRAGSuperComponent(
        document_store=document_store,
        embedder_model="text-embedding-3-small",
        llm_model="gpt-4o-mini",
        top_k=3,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Example usage
    query = "What is artificial intelligence?"
    result = naive_rag_sc.run(query=query)
    print("Answer:", result["replies"][0])
    print("Retrieved documents:", len(result["documents"]))