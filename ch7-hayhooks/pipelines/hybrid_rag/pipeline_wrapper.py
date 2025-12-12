from typing import List, Dict, Any
import os

from hayhooks import BasePipelineWrapper, log, get_last_user_message
from haystack import Pipeline
from pathlib import Path

class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        """Initialize the hybrid RAG pipeline"""
        log.info("Setting up hybrid RAG pipeline...")
        
        pipeline_yaml = (Path(__file__).parent / "rag.yml").read_text()
        
        self.pipeline = Pipeline.loads(pipeline_yaml)
        log.info("Hybrid RAG pipeline setup complete")
    
    
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
            # Both text embedders need the query text as input
            pipeline_inputs = {
                "text_embedder": {"text": query},
                "sparse_text_embedder": {"text": query},
                "ranker": {"query": query},
                "prompt_builder": {"question": query}
            }
            
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