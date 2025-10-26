
#!/usr/bin/env python3
"""
Generate synthetic test data using a knowledge graph and PDF documents.

Usage from ch4 directory:
uv run python jupyter-notebooks/scripts/synthetictest.py \
    --data-path jupyter-notebooks/data_for_indexing \
    --kg-path jupyter-notebooks/data_for_eval/my_knowledge_graph.json \
    --output jupyter-notebooks/data_for_eval/synthetic_qa_pairs.csv

This script will:
1. Read the knowledge graph from data_for_eval directory
2. Generate synthetic question-answer pairs
3. Save the results in the data_for_eval directory
"""

import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("./.env")

from ragas.testset.graph import KnowledgeGraph
from ragas.testset import TestsetGenerator
from ragas.testset.synthesizers import (
    SingleHopSpecificQuerySynthesizer,
    MultiHopAbstractQuerySynthesizer,
    MultiHopSpecificQuerySynthesizer
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import PyMuPDFLoader

def generate_synthetic_tests(data_path: str, kg_path: str, output_path: str):
    """
    Generate synthetic test data using a knowledge graph and PDF documents.
    
    Args:
        data_path (str): Path to the directory containing PDF documents
        kg_path (str): Path to the knowledge graph JSON file
        output_path (str): Path where to save the generated test set CSV
    """
    # Validate inputs using absolute paths
    data_path = os.path.abspath(data_path)
    kg_path = os.path.abspath(kg_path)
    output_path = os.path.abspath(output_path)
    
    if not os.path.exists(data_path):
        raise ValueError(f"Data directory not found: {data_path}")
    if not os.path.exists(kg_path):
        raise ValueError(f"Knowledge graph file not found: {kg_path}")
    
    print(f"Using data directory: {data_path}")
    print(f"Using knowledge graph: {kg_path}")
    print(f"Output will be saved to: {output_path}")
    
    print("\nChecking OpenAI API access...")
    try:
        # Test API connection first
        test_llm = ChatOpenAI(model="gpt-4-1106-preview")  # Using a known valid model
        test_llm.invoke("Test connection to OpenAI API")
    except Exception as e:
        raise ConnectionError(f"Failed to connect to OpenAI API. Please check your API key and connection. Error: {str(e)}")
    
    print("API connection successful. Initializing models...")
    generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4.1-nano"))
    generator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
    
    print(f"Loading knowledge graph from {kg_path}...")
    usecase_data_kg = KnowledgeGraph.load(kg_path)
    
    print(f"Loading documents from {data_path}...")
    loader = DirectoryLoader(data_path, glob="*.pdf", loader_cls=PyMuPDFLoader)
    docs = loader.load()
    
    if not docs:
        raise ValueError(f"No PDF documents found in {data_path}")
    
    print("Creating test generator...")
    generator = TestsetGenerator(
        llm=generator_llm,
        embedding_model=generator_embeddings,
        knowledge_graph=usecase_data_kg
    )
    
    query_distribution = [
        (SingleHopSpecificQuerySynthesizer(llm=generator_llm), 0.5),
        (MultiHopAbstractQuerySynthesizer(llm=generator_llm), 0.25),
        (MultiHopSpecificQuerySynthesizer(llm=generator_llm), 0.25),
    ]
    
    print("Generating test set using knowledge graph...")
    testset = generator.generate(testset_size=10, query_distribution=query_distribution)
    testset.to_pandas()
    
    print("Generating test set using documents...")
    doc_generator = TestsetGenerator(llm=generator_llm, embedding_model=generator_embeddings)
    dataset = doc_generator.generate_with_langchain_docs(docs, testset_size=10)
    dataset.to_pandas()
    
    print(f"Saving test set to {output_path}...")
    dataset.to_csv(output_path)
    print("Done!")

def ensure_directory_exists(file_path: str) -> None:
    """Ensure the directory for the given file path exists."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic test data using knowledge graph and documents.')
    parser.add_argument(
        '--data-path',
        type=str,
        required=True,
        help='Path to the directory containing PDF documents (e.g., jupyter-notebooks/data_for_indexing)'
    )
    parser.add_argument(
        '--kg-path',
        type=str,
        required=True,
        help='Path to the knowledge graph JSON file (e.g., jupyter-notebooks/data_for_eval/my_knowledge_graph.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path where to save the generated test set CSV file (e.g., jupyter-notebooks/data_for_eval/synthetic_qa_pairs.csv)'
    )
    
    args = parser.parse_args()
    
    # Convert to absolute paths if they're not already
    base_dir = os.getcwd()
    data_path = os.path.join(base_dir, args.data_path)
    kg_path = os.path.join(base_dir, args.kg_path)
    output_path = os.path.join(base_dir, args.output)
    
    try:
        # Ensure output directory exists
        ensure_directory_exists(output_path)
        
        # Generate synthetic tests
        generate_synthetic_tests(data_path, kg_path, output_path)
    except ConnectionError as e:
        print(f"Connection Error: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if OPENAI_API_KEY is set in your .env file")
        print("2. Verify your internet connection")
        print("3. Ensure your API key has sufficient quota")
        print("4. Check if OpenAI's API status is green at: https://status.openai.com")
        exit(1)
    except ValueError as e:
        print(f"Input Error: {e}")
        print("\nPlease check the provided paths and try again.")
        exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        print("\nPlease report this issue if it persists.")
        exit(1)

if __name__ == "__main__":
    main()