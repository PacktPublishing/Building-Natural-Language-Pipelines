import wandb
import tiktoken
from typing import Dict, List, Any
import numpy as np
import pandas as pd

class RAGAnalytics:
    """Simplified analytics class for RAG evaluation results and W&B logging."""
    
    def __init__(self, results: Dict[str, Any], model_name: str = "gpt-4o-mini", embedding_models: List[str] = None):
        self.results = results
        self.model_name = model_name
        self.embedding_models = embedding_models or ["text-embedding-3-small", "text-embedding-3-large"]
        self.evaluation_df = results['evaluation_df']
        
        # Current OpenAI pricing (per 1M tokens as of November 2024)
        self.pricing = {
            # Current GPT Models (Standard tier pricing)
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4o-2024-05-13": {"input": 5.00, "output": 15.00},
            "o1": {"input": 15.00, "output": 60.00},
            "o1-mini": {"input": 3.00, "output": 12.00},
            "o1-preview": {"input": 15.00, "output": 60.00},
            "o3-mini": {"input": 1.10, "output": 4.40},
            "o3": {"input": 2.00, "output": 8.00},
            
            # Legacy Models
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            
            # Embedding Models (per 1M tokens)
            "text-embedding-3-small": {"embed": 0.02},
            "text-embedding-3-large": {"embed": 0.13},
            "text-embedding-ada-002": {"embed": 0.10}
        }
        # Initialize tokenizer
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        self.token_usage = self._calculate_token_usage()
        self.embedding_usage = self._calculate_embedding_usage()
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
    
    def _calculate_embedding_usage(self) -> Dict[str, Any]:
        """Calculate embedding token usage for different embedding models."""
        embedding_usage = {}
        
        # Estimate tokens used for embedding generation
        # This includes the input text that gets embedded during RAG indexing and retrieval
        total_embedding_tokens = 0
        embedding_operations = 0
        
        for _, row in self.evaluation_df.iterrows():
            # Count tokens from input query (gets embedded for retrieval)
            query_tokens = len(self.tokenizer.encode(row['user_input']))
            
            # Count tokens from retrieved contexts (were embedded during indexing)
            context_tokens = 0
            if 'retrieved_contexts' in row and row['retrieved_contexts']:
                for context in row['retrieved_contexts']:
                    context_tokens += len(self.tokenizer.encode(str(context)))
            
            total_embedding_tokens += query_tokens + context_tokens
            embedding_operations += 1 + len(row.get('retrieved_contexts', []))
        
        # Calculate costs for each embedding model
        for model in self.embedding_models:
            if model in self.pricing:
                model_cost = (total_embedding_tokens / 1_000_000) * self.pricing[model]["embed"]
                embedding_usage[f"{model}_tokens"] = total_embedding_tokens
                embedding_usage[f"{model}_cost"] = model_cost
        
        embedding_usage["total_embedding_operations"] = embedding_operations
        embedding_usage["average_tokens_per_operation"] = total_embedding_tokens / max(1, embedding_operations)
        
        return embedding_usage
    
    def _calculate_costs(self) -> Dict[str, Any]:
        """Calculate estimated API costs per query including LLM and embedding costs."""
        model_pricing = self.pricing.get(self.model_name, self.pricing["gpt-4o-mini"])
        
        # LLM costs (per 1M tokens, convert to per token)
        input_costs = [(tokens / 1_000_000) * model_pricing["input"] for tokens in self.token_usage["input_tokens"]]
        output_costs = [(tokens / 1_000_000) * model_pricing["output"] for tokens in self.token_usage["output_tokens"]]
        llm_costs = [i + o for i, o in zip(input_costs, output_costs)]
        
        # Embedding costs per query (distributed across all queries)
        num_queries = len(self.token_usage["input_tokens"])
        embedding_cost_per_query = {}
        total_embedding_cost = 0
        
        for model in self.embedding_models:
            if f"{model}_cost" in self.embedding_usage:
                cost_per_query = self.embedding_usage[f"{model}_cost"] / max(1, num_queries)
                embedding_cost_per_query[model] = cost_per_query
                total_embedding_cost += self.embedding_usage[f"{model}_cost"]
        
        # Total costs per query (LLM + share of embedding costs)
        embedding_cost_per_query_total = total_embedding_cost / max(1, num_queries)
        total_costs = [llm + embedding_cost_per_query_total for llm in llm_costs]
        
        return {
            "input_costs": input_costs,
            "output_costs": output_costs, 
            "llm_costs": llm_costs,
            "embedding_costs": embedding_cost_per_query,
            "total_embedding_cost": total_embedding_cost,
            "embedding_cost_per_query": embedding_cost_per_query_total,
            "total_costs": total_costs
        }
        
    def log_to_wandb(self, run: wandb.init) -> Dict[str, Any]:
        """Calculates summary analytics and logs to W&B with meaningful plots including embedding costs."""
        total_cost = sum(self.costs['total_costs'])
        total_llm_cost = sum(self.costs['llm_costs'])
        total_embedding_cost = self.costs['total_embedding_cost']
        total_tokens = sum(self.token_usage['total_tokens'])
        num_queries = len(self.token_usage['total_tokens'])
        
        # Enhanced summary metrics including embedding analytics
        summary_metrics = {
            # Overall costs
            "total_cost_usd": total_cost,
            "llm_cost_usd": total_llm_cost,
            "embedding_cost_usd": total_embedding_cost,
            "average_cost_per_query_usd": np.mean(self.costs['total_costs']),
            
            # LLM metrics
            "average_llm_tokens_per_query": np.mean(self.token_usage['total_tokens']),
            "average_input_tokens_per_query": np.mean(self.token_usage['input_tokens']),
            "average_output_tokens_per_query": np.mean(self.token_usage['output_tokens']),
            
            # Embedding metrics
            "total_embedding_operations": self.embedding_usage.get('total_embedding_operations', 0),
            "average_embedding_tokens_per_operation": self.embedding_usage.get('average_tokens_per_operation', 0),
            
            # Efficiency metrics
            "token_efficiency_tps_per_dollar": total_tokens / total_cost if total_cost > 0 else 0,
            "cost_breakdown_llm_percentage": (total_llm_cost / total_cost * 100) if total_cost > 0 else 0,
            "cost_breakdown_embedding_percentage": (total_embedding_cost / total_cost * 100) if total_cost > 0 else 0,
            
            # Model information
            "llm_model": self.model_name,
            "embedding_models": ", ".join(self.embedding_models),
        }
        
        # Add per-embedding-model costs
        for model in self.embedding_models:
            if f"{model}_cost" in self.embedding_usage:
                summary_metrics[f"{model}_cost_usd"] = self.embedding_usage[f"{model}_cost"]
                summary_metrics[f"{model}_tokens"] = self.embedding_usage[f"{model}_tokens"]
        
        # Prepare enhanced DataFrame for logging
        analysis_df = self.evaluation_df.copy()
        analysis_df['total_cost_usd'] = self.costs['total_costs']
        analysis_df['llm_cost_usd'] = self.costs['llm_costs']
        analysis_df['embedding_cost_usd'] = self.costs['embedding_cost_per_query']
        analysis_df['total_tokens'] = self.token_usage['total_tokens']
        analysis_df['input_tokens'] = self.token_usage['input_tokens']
        analysis_df['output_tokens'] = self.token_usage['output_tokens']
        
        # Log detailed table (top 10)
        run.log({"detailed_query_analysis": wandb.Table(dataframe=analysis_df.head(10))})
        
        # Log cost breakdown chart
        cost_breakdown_data = {
            "Cost Type": ["LLM", "Embeddings"],
            "Cost (USD)": [total_llm_cost, total_embedding_cost],
            "Percentage": [
                (total_llm_cost / total_cost * 100) if total_cost > 0 else 0,
                (total_embedding_cost / total_cost * 100) if total_cost > 0 else 0
            ]
        }
        run.log({"cost_breakdown": wandb.Table(dataframe=pd.DataFrame(cost_breakdown_data))})
        
        # Log embedding model comparison if multiple models
        if len(self.embedding_models) > 1:
            embedding_comparison = []
            for model in self.embedding_models:
                if f"{model}_cost" in self.embedding_usage:
                    embedding_comparison.append({
                        "Model": model,
                        "Total Cost (USD)": self.embedding_usage[f"{model}_cost"],
                        "Total Tokens": self.embedding_usage[f"{model}_tokens"],
                        "Cost per 1M Tokens": self.pricing[model]["embed"]
                    })
            
            if embedding_comparison:
                run.log({"embedding_model_comparison": wandb.Table(dataframe=pd.DataFrame(embedding_comparison))})
        
        # Log summary metrics to the run
        run.log(summary_metrics)
        
        print(f"Analytics: Logged comprehensive analysis for {num_queries} queries.")
        print(f"Total Cost: ${total_cost:.6f} (LLM: ${total_llm_cost:.6f}, Embeddings: ${total_embedding_cost:.6f})")
        print(f"Embedding Models: {', '.join(self.embedding_models)}")
        
        return summary_metrics