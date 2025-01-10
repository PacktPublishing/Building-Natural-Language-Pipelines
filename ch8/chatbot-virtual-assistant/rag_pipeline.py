from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack_integrations.components.retrievers.elasticsearch import ElasticsearchEmbeddingRetriever
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack import Pipeline 

class RAGPipeline:
    def __init__(self):
        """Initialize RAG Pipeline reading data from ElasticSearch instance"""
        
        # Initialize prompt template to read the documents in document store
        template = [ChatMessage.from_system("""
                            Answer the questions based on the given context.

                            Context:
                            {% for document in documents %}
                                {{ document.content }}
                            {% endfor %}
                            Question: {{ question }}
                            Answer:
                """)]
        # Initialize document store
        document_store = ElasticsearchDocumentStore(hosts = "http://localhost:9200",
                                            embedding_similarity_function='cosine')
        # Initialize components
        query_embedder = SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
        query_retriever = ElasticsearchEmbeddingRetriever(document_store=document_store)
        prompt_builder = ChatPromptBuilder(template=template)
        llm = OpenAIChatGenerator(model="gpt-4o-mini")

        # Inititalize pipeline
        self.rag_pipe = Pipeline()
        # Add components
        self.rag_pipe.add_component(instance= query_embedder, name = "embedder" )
        self.rag_pipe.add_component(instance=query_retriever, name="retriever")
        self.rag_pipe.add_component(instance=prompt_builder, name="prompt_builder")
        self.rag_pipe.add_component(instance=llm, name="llm" )
        # Connect components
        self.rag_pipe.connect("embedder.embedding", "retriever.query_embedding")
        self.rag_pipe.connect("retriever", "prompt_builder.documents")
        self.rag_pipe.connect("prompt_builder.prompt", "llm.messages")
        

    def run(self, query):
        """Add execution method and return response"""
        print("Drawing mermaid graph")
        self.rag_pipe.draw("rag_pipeline.png")
        return self.rag_pipe.run({"embedder": {"text": query}, "prompt_builder": {"question": query}})


def rag_pipeline_func(query: str): 
    """Convert pipeline into tool"""
    rag_pipeline = RAGPipeline()
    result = rag_pipeline.run(query=query)

    return {"reply": result["llm"]["replies"][0].content}


tools = [
    {
        "type": "function",
        "function": {
            "name": "rag_pipeline_func",
            "description": "Get information about where people live",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to use in the search. Infer this from the user's message. It should be a question or a statement",
                    }
                },
                "required": ["query"],
            },
        },
    },
]

