from typing import List, Dict, Any
import os

from hayhooks import BasePipelineWrapper, log, get_last_user_message
from haystack import Pipeline
from haystack.components.embedders import OpenAITextEmbedder
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.components.joiners import DocumentJoiner
from haystack.components.rankers import SentenceTransformersSimilarityRanker
from haystack.utils import Secret
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack_integrations.components.retrievers.elasticsearch import (
    ElasticsearchBM25Retriever,
    ElasticsearchEmbeddingRetriever
)


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        """Initialize the hybrid RAG pipeline"""
        log.info("Setting up hybrid RAG pipeline...")
        
        # Initialize document store (same as indexing)
        document_store = ElasticsearchDocumentStore(
            hosts=os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200"),
            index="small_embeddings"
        )
        
        # Build the pipeline exactly as in your HybridRAGSuperComponent
        self.pipeline = self._build_hybrid_rag_pipeline(document_store)
        log.info("Hybrid RAG pipeline setup complete")
    
    def _build_hybrid_rag_pipeline(self, document_store):
        """Build the hybrid RAG pipeline with all components"""
        pipeline = Pipeline()
        
        # Core components
        text_embedder = OpenAITextEmbedder(
            api_key=Secret.from_env_var("OPENAI_API_KEY"),
            model="text-embedding-3-small"
        )
        
        embedding_retriever = ElasticsearchEmbeddingRetriever(
            document_store=document_store,
            top_k=3
        )
        
        bm25_retriever = ElasticsearchBM25Retriever(
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
        pipeline.add_component("embedding_retriever", embedding_retriever)
        pipeline.add_component("bm25_retriever", bm25_retriever)
        pipeline.add_component("document_joiner", document_joiner)
        pipeline.add_component("ranker", ranker)
        pipeline.add_component("prompt_builder", prompt_builder)
        pipeline.add_component("llm", llm)
        
        # Connect components
        pipeline.connect("text_embedder.embedding", "embedding_retriever.query_embedding")
        pipeline.connect("embedding_retriever.documents", "document_joiner.documents")
        pipeline.connect("bm25_retriever.documents", "document_joiner.documents")
        pipeline.connect("document_joiner.documents", "ranker.documents")
        pipeline.connect("ranker.documents", "prompt_builder.documents")
        pipeline.connect("prompt_builder.prompt", "llm.prompt")
        
        return pipeline
    
    def run_api(self, query: str) -> Dict[str, Any]:
        """
        Answer a question using hybrid retrieval (BM25 + embedding) and reranking.
        
        Args:
            query: The question to answer
            
        Returns:
            Dictionary with the answer and retrieved documents
        """
        log.info(f"Processing query: {query}")
        
        try:
            # Use the correct input mapping for hybrid RAG pipeline
            pipeline_inputs = {
                "text_embedder": {"text": query},
                "bm25_retriever": {"query": query},
                "ranker": {"query": query},
                "prompt_builder": {"question": query}
            }
            
            log.info(f"Running pipeline with inputs: {list(pipeline_inputs.keys())}")


            log.info(f"Running pipeline with inputs: {list(pipeline_inputs.keys())}")
            
            # Force include all component outputs in result
            result = self.pipeline.run(pipeline_inputs, include_outputs_from={"embedding_retriever", "bm25_retriever", "document_joiner", "ranker", "text_embedder", "llm"})
            log.info(f"Pipeline result keys: {list(result.keys())}")
            
            # Log detailed results for debugging
            for component_name in ["embedding_retriever", "bm25_retriever", "document_joiner", "ranker"]:
                if component_name in result:
                    component_result = result[component_name]
                    if isinstance(component_result, dict) and "documents" in component_result:
                        log.info(f"{component_name} found {len(component_result['documents'])} documents")
                    else:
                        log.info(f"{component_name} result structure: {type(component_result)} - {component_result}")
                else:
                    log.info(f"{component_name} not in result - component did not execute")
        

            answer = result["llm"]["replies"][0] if result["llm"]["replies"] else "No answer generated"
            
            # Get documents from ranker (final ranked results)
            documents = result.get("ranker", {}).get("documents", [])
            
            response = {
                "answer": answer,
                "query": query,
                "num_documents_retrieved": len(documents),
                "documents": [
                    {
                        "content": doc.content if hasattr(doc, 'content') else str(doc),
                        "score": getattr(doc, 'score', None),
                        "meta": getattr(doc, 'meta', {})
                    }
                    for doc in documents
                ]
            }
            
            log.info(f"Query processed successfully - {len(documents)} documents retrieved")
            return response
            
        except Exception as e:
            log.error(f"Error processing query: {str(e)}")
            return {
                "error": str(e),
                "query": query,
                "answer": None,
                "documents": []
            }
    
    def run_chat_completion(self, model: str, messages: list, body: dict) -> str:
        """OpenAI-compatible chat completion endpoint"""
        # Extract the user's question from messages
        question = get_last_user_message(messages)
        
        # Run the pipeline
        result = self.run_api(query=question)
        
        # Return the answer
        return result.get("answer", "I couldn't find an answer to your question.")