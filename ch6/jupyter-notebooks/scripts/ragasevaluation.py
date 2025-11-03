import pandas as pd
from pathlib import Path
from haystack import component
from typing import List, Optional, Dict, Any, Union
from haystack import SuperComponent
from ragas import EvaluationDataset, evaluate
from haystack.utils import Secret
import os
from ragas.llms import HaystackLLMWrapper
from haystack.components.generators import OpenAIGenerator


@component
class CSVReaderComponent:
    """Reads a CSV file into a Pandas DataFrame."""

    @component.output_types(data_frame=pd.DataFrame)
    def run(self, source: Union[str, Path]):
        """
        Reads the CSV file from the first source in the list.
        
        Args:
            sources: List of file paths to CSV files. Only the first file will be processed.
            
        Returns:
            dict: Dictionary containing the loaded DataFrame under 'data_frame' key.
            
        Raises:
            FileNotFoundError: If the file doesn't exist or can't be read.
            ValueError: If the DataFrame is empty after loading.
        """
        if not source:
            raise ValueError("No sources provided")
            

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
    """

    def __init__(self, rag_supercomponent: SuperComponent):
        # We store the pre-initialized SuperComponent
        self.rag_supercomponent = rag_supercomponent
        self.output_names = ["augmented_data_frame"]

    @component.output_types(augmented_data_frame=pd.DataFrame)
    def run(self, data_frame: pd.DataFrame):
        
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
    


# Note: Ensure ragas and its dependencies (like litellm or openai) are installed
@component
class RagasEvaluationComponent:
    """
    Prepares data for Ragas, runs the evaluation, and returns the metrics.
    """
    
    def __init__(self, 
                 metrics: Optional[List[Any]] = None,
                 ragas_llm: Optional[Any] = None):
        
        # Default metrics for RAG evaluation
        self.metrics = metrics
        
        # Ragas requires an LLM for evaluation, often provided through OpenAI or Anthropic.
        # It's best practice to use a strong model like gpt-4o-mini or gpt-4.
        if ragas_llm is None:
            # Assumes OPENAI_API_KEY is set in the environment
            self.ragas_llm = HaystackLLMWrapper(OpenAIGenerator(model="gpt-4o-mini",
                                                               api_key=Secret.from_env_var("OPENAI_API_KEY")))
        else:
            self.ragas_llm = ragas_llm

    @component.output_types(metrics=Dict[str, float], evaluation_df=pd.DataFrame)
    def run(self, augmented_data_frame: pd.DataFrame):
        
        # 1. Map columns to Ragas requirements - correct column mapping for SingleTurnSample
        ragas_data = pd.DataFrame({
            'user_input': augmented_data_frame['user_input'],
            'response': augmented_data_frame['response'], 
            'retrieved_contexts': augmented_data_frame['retrieved_contexts'],
            'reference': augmented_data_frame['reference'],
            'reference_contexts': augmented_data_frame['reference_contexts'].apply(eval)
        })

        print("Creating Ragas EvaluationDataset...")
        # 2. Create EvaluationDataset using from_pandas which handles the format correctly
        dataset = EvaluationDataset.from_pandas(ragas_data)

        print("Starting Ragas evaluation...")
        
        # 3. Run Ragas Evaluation
        # Pass the configured LLM to Ragas
        results = evaluate(
            dataset=dataset,
            metrics=self.metrics,
            llm=self.ragas_llm
        )
        

        results_df = results.to_pandas()
        
        print("Ragas evaluation complete.")
        print(f"Overall metrics: {results}")
        
        return {"metrics": results, "evaluation_df": results_df}