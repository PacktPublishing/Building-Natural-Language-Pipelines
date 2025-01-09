from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack_integrations.components.retrievers.elasticsearch import ElasticsearchEmbeddingRetriever
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack import Pipeline 


template = [ChatMessage.from_system("""
Answer the questions based on the given context.

Context:
{% for document in documents %}
    {{ document.content }}
{% endfor %}
Question: {{ question }}
Answer:
""")]
document_store = ElasticsearchDocumentStore(hosts = "http://localhost:9200",
                                    embedding_similarity_function='cosine')

query_embedder = SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
query_retriever = ElasticsearchEmbeddingRetriever(document_store=document_store)
prompt_builder = ChatPromptBuilder(template=template)
llm = OpenAIChatGenerator(model="gpt-4o-mini")


rag_pipe = Pipeline()
rag_pipe.add_component(instance= query_embedder, name = "embedder" )
rag_pipe.add_component(instance=query_retriever, name="retriever")
rag_pipe.add_component(instance=prompt_builder, name="prompt_builder")
rag_pipe.add_component(instance=llm, name="llm" )

rag_pipe.connect("embedder.embedding", "retriever.query_embedding")
rag_pipe.connect("retriever", "prompt_builder.documents")
rag_pipe.connect("prompt_builder.prompt", "llm.messages")


    
def rag_pipeline_func(query: str): 
    result = rag_pipe.run({"embedder": {"text": query}, "prompt_builder": {"question": query}})

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

