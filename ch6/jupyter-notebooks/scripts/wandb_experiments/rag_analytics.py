import wandb
import tiktoken
from typing import Dict, List, Any
import numpy as np

class RAGAnalytics:
    """Simplified analytics class for RAG evaluation results and W&B logging."""
    
    def __init__(self, results: Dict[str, Any], model_name: str = "gpt-4o-mini"):
        self.results = results
        self.model_name = model_name
        self.evaluation_df = results['evaluation_df']
        
        # Token pricing (approximate costs per 1K tokens as of 2024 for demonstration)
        self.pricing = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
        }
        # Initialize tokenizer
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        self.token_usage = self._calculate_token_usage()
        self.costs = self._calculate_costs()
    
    def _calculate_token_usage(self) -> Dict[str, List[int]]:
        """Calculate token usage based on context and response lengths."""
        input_tokens = []
        output_tokens = []
        
        for _, row in self.evaluation_df.iterrows():
            input_text = row['user_input']
            if 'retrieved_contexts' in row and row['retrieved_contexts']:
                context_text = " ".join(row['retrieved_contexts'])
                input_text += " " + context_text
            
            input_tokens.append(len(self.tokenizer.encode(input_text)))
            
            output_text = row['response'] if 'response' in row else ""
            output_tokens.append(len(self.tokenizer.encode(output_text)))
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": [i + o for i, o in zip(input_tokens, output_tokens)]
        }
    
    def _calculate_costs(self) -> Dict[str, List[float]]:
        """Calculate estimated API costs per query."""
        model_pricing = self.pricing.get(self.model_name, self.pricing["gpt-4o-mini"])
        
        input_costs = [(tokens / 1000) * model_pricing["input"] for tokens in self.token_usage["input_tokens"]]
        output_costs = [(tokens / 1000) * model_pricing["output"] for tokens in self.token_usage["output_tokens"]]
        total_costs = [i + o for i, o in zip(input_costs, output_costs)]
        
        return {"input_costs": input_costs, "output_costs": output_costs, "total_costs": total_costs}
        
    def log_to_wandb(self, run: wandb.init) -> Dict[str, Any]:
        """Calculates summary analytics and logs to W&B with meaningful plots."""
        total_cost = sum(self.costs['total_costs'])
        total_tokens = sum(self.token_usage['total_tokens'])
        num_queries = len(self.token_usage['total_tokens'])
        
        summary_metrics = {
            "total_cost_usd": total_cost,
            "average_cost_per_query_usd": np.mean(self.costs['total_costs']),
            "average_tokens_per_query": np.mean(self.token_usage['total_tokens']),
            "token_efficiency_tps_per_dollar": total_tokens / total_cost if total_cost > 0 else 0,
        }
        
        # Prepare DataFrame for logging
        analysis_df = self.evaluation_df.copy()
        analysis_df['total_cost_usd'] = self.costs['total_costs']
        analysis_df['total_tokens'] = self.token_usage['total_tokens']
        analysis_df['input_tokens'] = self.token_usage['input_tokens']
        
        # Log detailed table (top 10)
        run.log({"detailed_query_analysis": wandb.Table(dataframe=analysis_df.head(10))})
        
        
        # Log summary metrics to the run
        run.log(summary_metrics)
        
        print(f"Analytics: Logged comprehensive analysis for {num_queries} queries.")
        return summary_metrics