#!/usr/bin/env python3
"""
Create a knowledge graph from PDF documents in a specified directory.

# From the ch4 directory:
uv run python jupyter-notebooks/scripts/knowledgegraph.py --data-path jupyter-notebooks/data_for_indexing

# Or specify a custom output path:
uv run python jupyter-notebooks/scripts/knowledgegraph.py\
    --data-path jupyter-notebooks/data_for_indexing \
    --output jupyter-notebooks/data_for_eval/my_knowledge_graph.json
"""

import argparse
import os
from dotenv import load_dotenv
load_dotenv("./.env")

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from ragas.testset.graph import Node, NodeType
from ragas.testset.graph import KnowledgeGraph
from ragas.testset.transforms import default_transforms, apply_transforms

def create_knowledge_graph(data_path: str, output_path: str = None):
    """
    Create a knowledge graph from PDF documents in the specified directory.
    
    Args:
        data_path (str): Path to the directory containing PDF documents
        output_path (str, optional): Path where to save the knowledge graph JSON file
    """
    # Ensure the path exists
    if not os.path.exists(data_path):
        raise ValueError(f"Directory not found: {data_path}")
    
    # Initialize LLM and embeddings
    generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4.1-nano"))
    generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
    
    # Load documents
    loader = DirectoryLoader(data_path, glob="*.pdf", loader_cls=PyMuPDFLoader)
    docs = loader.load()
    
    if not docs:
        print(f"Warning: No PDF documents found in {data_path}")
        return
    
    # Create knowledge graph
    kg = KnowledgeGraph()
    
    for doc in docs:
        kg.nodes.append(
            Node(
                type=NodeType.DOCUMENT,
                properties={"page_content": doc.page_content, "document_metadata": doc.metadata}
            )
        )
    
    # Apply transforms
    transformer_llm = generator_llm
    embedding_model = generator_embeddings
    
    default_transforms_config = default_transforms(
        documents=docs, 
        llm=transformer_llm, 
        embedding_model=embedding_model
    )
    apply_transforms(kg, default_transforms_config)
    
    # Save the knowledge graph
    output_file = output_path if output_path else "usecase_data_kg.json"
    kg.save(output_file)
    print(f"Knowledge graph saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Create a knowledge graph from PDF documents.')
    parser.add_argument(
        '--data-path', 
        type=str, 
        required=True,
        help='Path to the directory containing PDF documents'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default=None,
        help='Path where to save the knowledge graph JSON file (default: usecase_data_kg.json)'
    )
    
    args = parser.parse_args()
    
    try:
        create_knowledge_graph(args.data_path, args.output)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()