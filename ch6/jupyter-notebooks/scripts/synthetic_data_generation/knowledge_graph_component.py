#!/usr/bin/env python3
"""
Haystack 2.0 custom component for creating knowledge graphs from LangChain documents.

This component takes a list of LangChain Document objects and creates a Ragas knowledge graph
with applied transforms for synthetic test generation and evaluation.
"""

from typing import List, Optional, Dict, Any
import os
from haystack import component, logging
from langchain_core.documents import Document as LangChainDocument

from ragas.llms import HaystackLLMWrapper
from haystack.components.generators import OpenAIGenerator
from ragas.embeddings import HaystackEmbeddingsWrapper
from haystack.components.embedders.openai_text_embedder import (
            OpenAITextEmbedder,
        )
from haystack.utils import Secret

from ragas.testset.graph import Node, NodeType, KnowledgeGraph
from ragas.testset.transforms import default_transforms, apply_transforms

from haystack.dataclasses import Document as HaystackDocument

logger = logging.getLogger(__name__)


@component
class KnowledgeGraphGenerator:
    """
    A Haystack 2.0 component that creates a knowledge graph from LangChain documents.
    
    This component converts LangChain Document objects into a Ragas KnowledgeGraph
    with applied transforms for enhanced synthetic test generation capabilities.
    
    Usage:
        ```python
        from knowledge_graph_component import KnowledgeGraphGenerator
        
        # Initialize the component
        kg_generator = KnowledgeGraphGenerator(
            llm_model="gpt-4o-mini",
            apply_transforms=True
        )
        
        # Use in a pipeline
        result = kg_generator.run(documents=langchain_docs)
        knowledge_graph = result["knowledge_graph"]
        ```
    """
    
    def __init__(
        self, 
        generator: Any,
        embedder: Any,
        apply_transforms: bool = True
    ):
        """
        Initialize the KnowledgeGraphGenerator component.
        
        Args:
            generator: LLM generator instance (e.g., OpenAIGenerator or OllamaGenerator).
            embedder: Text embedder instance (e.g., OpenAITextEmbedder or OllamaTextEmbedder).
            apply_transforms (bool): Whether to apply default transforms to enhance the knowledge graph.
        
        Example:
            ```python
            from haystack.components.generators import OpenAIGenerator
            from haystack.components.embedders.openai_text_embedder import OpenAITextEmbedder
            from haystack.utils import Secret
            
            generator = OpenAIGenerator(
                model="gpt-4o-mini",
                api_key=Secret.from_token(os.getenv("OPENAI_API_KEY"))
            )
            embedder = OpenAITextEmbedder(
                model="text-embedding-3-small",
                api_key=Secret.from_token(os.getenv("OPENAI_API_KEY"))
            )
            
            kg_generator = KnowledgeGraphGenerator(
                generator=generator,
                embedder=embedder,
                apply_transforms=True
            )
            ```
        """
        self.apply_transforms = apply_transforms
        
        # Wrap generators for Ragas compatibility
        self.generator_llm = HaystackLLMWrapper(generator)
        self.generator_embeddings = HaystackEmbeddingsWrapper(embedder=embedder)
        
        logger.info(f"Initialized KnowledgeGraphGenerator with provided generator and embedder")
    
    @component.output_types(knowledge_graph=KnowledgeGraph, node_count=int, transform_applied=bool)
    def run(self, documents: List[LangChainDocument]) -> dict:
        """
        Create a knowledge graph from the provided LangChain documents.
        
        Args:
            documents (List[LangChainDocument]): List of LangChain Document objects to process.
            
        Returns:
            dict: Contains:
                - knowledge_graph (KnowledgeGraph): The created knowledge graph
                - node_count (int): Number of document nodes created
                - transform_applied (bool): Whether transforms were applied
        """
        if not documents:
            logger.warning("No documents provided to KnowledgeGraphGenerator")
            return {
                "knowledge_graph": KnowledgeGraph(), 
                "node_count": 0, 
                "transform_applied": False
            }
        
        logger.info(f"Creating knowledge graph from {len(documents)} documents")
        
        # Create knowledge graph
        kg = KnowledgeGraph()
        
        # Add document nodes to the knowledge graph
        for doc in documents:
            kg.nodes.append(
                Node(
                    type=NodeType.DOCUMENT,
                    properties={
                        "page_content": doc.page_content, 
                        "document_metadata": doc.metadata
                    }
                )
            )
        
        node_count = len(kg.nodes)
        transform_applied = False
        
        # Apply transforms if requested
        if self.apply_transforms:
            try:
                logger.info("Applying default transforms to knowledge graph")
                
                transformer_llm = self.generator_llm
                embedding_model = self.generator_embeddings
                
                default_transforms_config = default_transforms(
                    documents=documents, 
                    llm=transformer_llm, 
                    embedding_model=embedding_model
                )
                apply_transforms(kg, default_transforms_config)
                transform_applied = True
                
                logger.info("Successfully applied transforms to knowledge graph")
                
            except Exception as e:
                logger.error(f"Failed to apply transforms: {e}")
                # Continue without transforms rather than failing completely
                logger.warning("Proceeding with knowledge graph without transforms")
        
        logger.info(f"Knowledge graph created with {node_count} document nodes, transforms applied: {transform_applied}")
        
        return {
            "knowledge_graph": kg,
            "node_count": node_count,
            "transform_applied": transform_applied
        }


@component 
class KnowledgeGraphSaver:
    """
    A Haystack 2.0 component that saves a knowledge graph to a JSON file.
    
    This component takes a KnowledgeGraph object and saves it to the specified file path.
    Can be used in pipelines after the KnowledgeGraphGenerator component.
    """
    
    def __init__(self, output_path: Optional[str] = None):
        """
        Initialize the KnowledgeGraphSaver component.
        
        Args:
            output_path (Optional[str]): Default output path for saving. Can be overridden at runtime.
        """
        self.default_output_path = output_path or "knowledge_graph.json"
    
    @component.output_types(saved_path=str, success=bool)
    def run(self, knowledge_graph: KnowledgeGraph, output_path: Optional[str] = None) -> dict:
        """
        Save the knowledge graph to a JSON file.
        
        Args:
            knowledge_graph (KnowledgeGraph): The knowledge graph to save.
            output_path (Optional[str]): Path where to save the file. Uses default if not provided.
            
        Returns:
            dict: Contains:
                - saved_path (str): The actual path where the file was saved
                - success (bool): Whether the save operation was successful
        """
        save_path = output_path or self.default_output_path
        
        try:
            knowledge_graph.save(save_path)
            logger.info(f"Knowledge graph successfully saved to: {save_path}")
            return {"saved_path": save_path, "success": True}
            
        except Exception as e:
            logger.error(f"Failed to save knowledge graph to {save_path}: {e}")
            return {"saved_path": save_path, "success": False}


"""# Example usage and pipeline creation
if __name__ == "__main__":

    import os
    from dotenv import load_dotenv
    from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
    from haystack import Pipeline
    
    # Load environment variables
    load_dotenv("./.env")
    
    # Example: Load documents (this would typically be done by other components in a real pipeline)
    data_path = "jupyter-notebooks/data_for_indexing"
    if os.path.exists(data_path):
        loader = DirectoryLoader(data_path, glob="*.pdf", loader_cls=PyMuPDFLoader)
        docs = loader.load()
        
        # Create and run the component
        kg_generator = KnowledgeGraphGenerator(apply_transforms=True)
        kg_saver = KnowledgeGraphSaver("example_knowledge_graph.json")
        
        # Create a simple pipeline
        pipeline = Pipeline()
        pipeline.add_component("kg_generator", kg_generator)
        pipeline.add_component("kg_saver", kg_saver)
        pipeline.connect("kg_generator.knowledge_graph", "kg_saver.knowledge_graph")
        
        # Run the pipeline
        result = pipeline.run({"kg_generator": {"documents": docs}})
        
        print(f"Pipeline completed. Results: {result}")
    else:
        print(f"Data path {data_path} not found. Please check the path.")
"""