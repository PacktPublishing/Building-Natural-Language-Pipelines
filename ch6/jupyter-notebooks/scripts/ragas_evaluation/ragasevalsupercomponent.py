"""
RAGAS Evaluation SuperComponent for Systematic RAG Comparison

This module contains custom Haystack components for evaluating RAG systems using the RAGAS framework.
It provides a systematic pipeline for comparing different RAG approaches with consistent evaluation conditions.

Components:
1. CSVReaderComponent: Loads evaluation datasets from CSV files
2. RAGDataAugmenterComponent: Processes queries through RAG SuperComponents
3. RagasEvaluationComponent: Evaluates RAG outputs using RAGAS metrics
4. RAGEvaluationSuperComponent: Complete evaluation pipeline

Author: Building Natural Language Pipelines - Chapter 6
"""

import pandas as pd
from pathlib import Path
from haystack import component, Pipeline, SuperComponent, super_component
from typing import List, Optional, Dict, Any, Union
import os

# RAGAS imports
from ragas import EvaluationDataset, evaluate
from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness, ResponseRelevancy
from ragas.llms import HaystackLLMWrapper
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret


@component
class CSVReaderComponent:
    """
    Reads a CSV file into a Pandas DataFrame.
    
    This component serves as the entry point for evaluation pipelines,
    handling loading of synthetic evaluation datasets with robust error handling.
    
    Key Features:
    - Robust Error Handling: Validates file existence and data integrity
    - Pandas Integration: Returns data as DataFrame for easy manipulation
    - Pipeline Compatible: Designed to work seamlessly with Haystack pipelines
    """

    @component.output_types(data_frame=pd.DataFrame)
    def run(self, source: Union[str, Path]):
        """
        Reads the CSV file from the specified source.
        
        Args:
            source: File path to CSV file to process.
            
        Returns:
            dict: Dictionary containing the loaded DataFrame under 'data_frame' key.
            
        Raises:
            FileNotFoundError: If the file doesn't exist or can't be read.
            ValueError: If the DataFrame is empty after loading.
        """
        if not source:
            raise ValueError("No source provided")

        try:
            df = pd.read_csv(source)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found at {source}")
        except Exception as e:
            raise ValueError(f"Error reading CSV file {source}: {str(e)}")

        # Check if DataFrame is empty using proper pandas method
        if df.empty:
            raise ValueError(f"DataFrame is empty after loading from {source}")

        print(f"Loaded DataFrame with {len(df)} rows from {source}.")
        return {"data_frame": df}


@component
class RAGDataAugmenterComponent:
    """
    Applies a RAG SuperComponent to each query in a DataFrame and 
    augments the data with the generated answer and retrieved contexts.
    
    This component is the core of the evaluation workflow, taking each query 
    from the evaluation dataset and processing it through a RAG SuperComponent,
    collecting both generated responses and retrieved contexts.
    
    Key Design Features:
    - SuperComponent Flexibility: Accepts any pre-configured RAG SuperComponent
    - Batch Processing: Efficiently processes entire evaluation datasets
    - Data Augmentation: Enriches original dataset with RAG outputs for evaluation
    - Context Extraction: Captures retrieved documents for context-based metrics
    """

    def __init__(self, rag_supercomponent: SuperComponent):
        """
        Initialize the RAG Data Augmenter with a RAG SuperComponent.
        
        Args:
            rag_supercomponent: Pre-initialized RAG SuperComponent to evaluate
        """
        # We store the pre-initialized SuperComponent
        self.rag_supercomponent = rag_supercomponent
        self.output_names = ["augmented_data_frame"]

    @component.output_types(augmented_data_frame=pd.DataFrame)
    def run(self, data_frame: pd.DataFrame):
        """
        Process each query through the RAG SuperComponent and augment the data.
        
        Args:
            data_frame: DataFrame containing evaluation queries and ground truth
            
        Returns:
            dict: Dictionary with augmented DataFrame containing RAG responses and contexts
        """
        # New columns to store RAG results
        answers: List[str] = []
        contexts: List[List[str]] = []

        print(f"Running RAG SuperComponent on {len(data_frame)} queries...")

        # Iterate through the queries (user_input column)
        for _, row in data_frame.iterrows():
            query = row["user_input"]
            
            # 1. Run the RAG SuperComponent
            # It expects 'query' as input and returns a dictionary.
            rag_output = self.rag_supercomponent.run(query=query)
            
            # 2. Extract answer and contexts
            # Based on the naive_rag_sc/hybrid_rag_sc structure:
            answer = rag_output.get('replies', [''])[0]
            
            # Extract content from the Document objects
            retrieved_docs = rag_output.get('documents', [])
            retrieved_contexts = [doc.content for doc in retrieved_docs]
            
            answers.append(answer)
            contexts.append(retrieved_contexts)
        
        # 3. Augment the DataFrame
        data_frame['response'] = answers
        data_frame['retrieved_contexts'] = contexts
        
        print("RAG processing complete.")
        return {"augmented_data_frame": data_frame}


@component
class RagasEvaluationComponent:
    """
    Integrates the RAGAS framework into Haystack pipeline for systematic evaluation.
    
    This component provides systematic evaluation metrics for RAG systems using
    the RAGAS framework with focus on core metrics for reliable comparison.
    
    Core Evaluation Metrics:
    - Faithfulness: Factual consistency with retrieved context
    - ResponseRelevancy: How well responses answer the questions  
    - LLMContextRecall: How well retrieval captures relevant information
    - FactualCorrectness: Correctness of factual claims in responses
    
    Technical Features:
    - Focused Metrics: Core metrics for reliable comparison
    - LLM Integration: Uses OpenAI GPT models for evaluation judgments
    - Data Format Handling: Automatically formats data for RAGAS requirements
    - Comprehensive Output: Returns both aggregated metrics and detailed per-query results
    """
    
    def __init__(self, 
                 metrics: Optional[List[Any]] = None,
                 llm_model: str = "gpt-4o-mini",
                 openai_api_key: Optional[str] = None):
        """
        Initialize the RAGAS Evaluation Component.
        
        Args:
            metrics: List of RAGAS metrics to evaluate (defaults to core metrics)
            llm_model (str): OpenAI model for evaluation. Defaults to "gpt-4o-mini".
            openai_api_key (Optional[str]): OpenAI API key. If None, will use environment variable.
        """
        
        # Default to core metrics for systematic comparison
        if metrics is None:
            self.metrics = [
                Faithfulness(), 
                ResponseRelevancy(),
                LLMContextRecall(),
                FactualCorrectness()
            ]
        else:
            self.metrics = metrics
            
        self.llm_model = llm_model
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")
        
        # Configure RAGAS LLM for evaluation
        self.ragas_llm = HaystackLLMWrapper(
            OpenAIGenerator(
                model=self.llm_model,
                api_key=Secret.from_token(self.openai_api_key)
            )
        )

    @component.output_types(metrics=Dict[str, float], evaluation_df=pd.DataFrame)
    def run(self, augmented_data_frame: pd.DataFrame):
        """
        Run RAGAS evaluation on augmented dataset.
        
        Args:
            augmented_data_frame: DataFrame with RAG responses and retrieved contexts
            
        Returns:
            dict: Dictionary containing evaluation metrics and detailed results DataFrame
        """
        
        # 1. Map columns to Ragas requirements
        ragas_data = pd.DataFrame({
            'user_input': augmented_data_frame['user_input'],
            'response': augmented_data_frame['response'], 
            'retrieved_contexts': augmented_data_frame['retrieved_contexts'],
            'reference': augmented_data_frame['reference'],
            'reference_contexts': augmented_data_frame['reference_contexts'].apply(eval)
        })

        print("Creating Ragas EvaluationDataset...")
        # 2. Create EvaluationDataset
        dataset = EvaluationDataset.from_pandas(ragas_data)

        print("Starting Ragas evaluation...")
        
        # 3. Run Ragas Evaluation
        results = evaluate(
            dataset=dataset,
            metrics=self.metrics,
            llm=self.ragas_llm
        )
        
        results_df = results.to_pandas()
        
        print("Ragas evaluation complete.")
        print(f"Overall metrics: {results}")
        
        return {"metrics": results, "evaluation_df": results_df}


@super_component
class RAGEvaluationSuperComponent:
    """
    Complete RAG evaluation pipeline for systematic comparison of RAG systems.
    
    This SuperComponent provides a systematic evaluation workflow for comparing
    RAG approaches with consistent evaluation conditions and comprehensive metrics.
    
    Pipeline Flow:
    CSV Data → RAGDataAugmenter → RagasEvaluation → Metrics & Results
    
    Key Benefits:
    - Systematic: Same evaluation conditions for all RAG systems
    - Reproducible: Consistent evaluation across experiments
    - Scalable: Easy to add new RAG implementations
    - Comprehensive: Multiple metrics provide complete assessment
    """
    
    def __init__(self, 
                 rag_supercomponent, 
                 system_name: str,
                 llm_model: str = "gpt-4o-mini",
                 openai_api_key: Optional[str] = None):
        """
        Initialize the RAG Evaluation SuperComponent.
        
        Args:
            rag_supercomponent: The RAG system to evaluate
            system_name (str): Name for logging and identification
            llm_model (str): OpenAI model for evaluation. Defaults to "gpt-4o-mini".
            openai_api_key (Optional[str]): OpenAI API key. If None, will use environment variable.
        """
        self.rag_supercomponent = rag_supercomponent
        self.system_name = system_name
        self.llm_model = llm_model
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")
        
        self._build_pipeline()
    
    def _build_pipeline(self):
        """Build the RAG evaluation pipeline with initialized components."""
        
        print(f"\n🔄 Building evaluation pipeline for {self.system_name}...")
        print("=" * 50)
        
        # --- 1. Initialize Evaluation Pipeline Components ---
        
        # CSV Reader: Loads evaluation dataset
        reader = CSVReaderComponent()
        
        # RAG Data Augmenter: Processes queries through the RAG system
        augmenter = RAGDataAugmenterComponent(rag_supercomponent=self.rag_supercomponent)
        
        # RAGAS Evaluator: Computes evaluation metrics
        evaluator = RagasEvaluationComponent(
            llm_model=self.llm_model,
            openai_api_key=self.openai_api_key
        )
        
        # --- 2. Build the Evaluation Pipeline ---
        self.pipeline = Pipeline()
        
        # Add all components to the pipeline
        self.pipeline.add_component("reader", reader)
        self.pipeline.add_component("augmenter", augmenter)
        self.pipeline.add_component("evaluator", evaluator)
        
        # --- 3. Connect the Components in a Graph ---
        
        # CSV Data -> RAG Augmentation -> RAGAS Evaluation
        self.pipeline.connect("reader.data_frame", "augmenter.data_frame")
        self.pipeline.connect("augmenter.augmented_data_frame", "evaluator.augmented_data_frame")
        
        # --- 4. Define Input and Output Mappings ---
        self.input_mapping = {
            "csv_source": ["reader.source"]
        }

        self.output_mapping = {
            "evaluator.metrics": "metrics",
            "evaluator.evaluation_df": "evaluation_df"
        }
        
        print(f"✅ Evaluation pipeline for {self.system_name} built successfully!")


# Example usage and utility functions
def create_comparison_report(naive_results: Dict[str, Any], 
                           hybrid_results: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a comprehensive comparison report between two RAG systems.
    
    Args:
        naive_results: Evaluation results from Naive RAG system
        hybrid_results: Evaluation results from Hybrid RAG system
        
    Returns:
        pd.DataFrame: Comparison report with metrics, improvements, and analysis
    """
    # Extract metrics from both evaluations
    naive_metrics = naive_results['metrics']
    hybrid_metrics = hybrid_results['metrics']
    
    # Get individual scores for statistical analysis
    naive_scores = naive_metrics.scores
    hybrid_scores = hybrid_metrics.scores
    
    # Compute averages for each metric
    naive_df = pd.DataFrame(naive_scores)
    hybrid_df = pd.DataFrame(hybrid_scores)
    
    naive_averages = naive_df.mean()
    hybrid_averages = hybrid_df.mean()
    
    # Create comparison DataFrame
    comparison_data = {
        'Metric': list(naive_averages.index),
        'Naive RAG': list(naive_averages.values),
        'Hybrid RAG': list(hybrid_averages.values)
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df['Improvement (%)'] = ((comparison_df['Hybrid RAG'] - comparison_df['Naive RAG']) / comparison_df['Naive RAG'] * 100).round(2)
    comparison_df['Better System'] = comparison_df.apply(
        lambda row: '🏆 Hybrid RAG' if row['Hybrid RAG'] > row['Naive RAG'] 
        else '🏆 Naive RAG' if row['Naive RAG'] > row['Hybrid RAG'] 
        else '🤝 Tie', axis=1
    )
    
    # Round scores for better display
    comparison_df['Naive RAG'] = comparison_df['Naive RAG'].round(4)
    comparison_df['Hybrid RAG'] = comparison_df['Hybrid RAG'].round(4)
    
    return comparison_df



