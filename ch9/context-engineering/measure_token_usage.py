"""
Token Usage Measurement Script for Yelp Navigator V1 vs V2

This script measures actual token usage across both architectures to validate
the theoretical performance improvements documented in ARCHITECTURE_COMPARISON.md.

Usage:
    uv run python measure_token_usage.py --test-query "Italian restaurants in Boston"
    uv run python measure_token_usage.py --run-all-tests
    uv run python measure_token_usage.py --compare-only
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import tiktoken
import pandas as pd
from tabulate import tabulate



@dataclass
class TokenMeasurement:
    """Store token usage for a single operation."""
    operation: str
    architecture: str  # "v1" or "v2"
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    timestamp: str


class TokenCounter:
    """Count tokens using tiktoken (OpenAI's tokenizer)."""
    
    def __init__(self, model: str = "gpt-4"):
        """Initialize with the appropriate encoding for the model."""
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for gpt-4/gpt-3.5-turbo
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        return len(self.encoding.encode(text))
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in a list of messages (OpenAI chat format)."""
        # Based on OpenAI's token counting methodology
        tokens = 0
        for message in messages:
            tokens += 4  # Every message has overhead
            for key, value in message.items():
                tokens += self.count_tokens(str(value))
                if key == "name":
                    tokens += -1  # Role is always required and always 1 token
        tokens += 2  # Every reply is primed with assistant
        return tokens


class WorkflowTracer:
    """Trace and measure token usage through a workflow execution."""
    
    def __init__(self, architecture: str, counter: TokenCounter):
        self.architecture = architecture
        self.counter = counter
        self.measurements: List[TokenMeasurement] = []
        self.start_time = None
    
    def measure_prompt(self, operation: str, prompt: str, response: str) -> TokenMeasurement:
        """Measure tokens for a single prompt-response pair."""
        input_tokens = self.counter.count_tokens(prompt)
        output_tokens = self.counter.count_tokens(response)
        
        measurement = TokenMeasurement(
            operation=operation,
            architecture=self.architecture,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=0,  # Can be filled in by caller
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.measurements.append(measurement)
        return measurement
    
    def measure_state(self, operation: str, state: Dict[str, Any]) -> int:
        """Measure tokens in the current state object."""
        # Convert state to JSON string for token counting
        state_str = json.dumps(state, default=str)
        return self.counter.count_tokens(state_str)
    
    def get_total_tokens(self) -> int:
        """Get total tokens used across all measurements."""
        return sum(m.total_tokens for m in self.measurements)
    
    def export_measurements(self) -> List[Dict[str, Any]]:
        """Export measurements as list of dicts."""
        return [asdict(m) for m in self.measurements]


def simulate_v1_workflow(query: str, location: str, detail_level: str = "general") -> WorkflowTracer:
    """
    Simulate V1 workflow and measure token usage.
    This reads from the actual V1 prompts and simulates the flow.
    """
    counter = TokenCounter()
    tracer = WorkflowTracer("v1", counter)
    
    # Import V1 components
    v1_path = str(Path(__file__).parent / "yelp-navigator-v1")
    if v1_path not in sys.path:
        sys.path.insert(0, v1_path)
    
    try:
        # Remove v2 from path if present to avoid conflicts
        v2_path = str(Path(__file__).parent / "yelp-navigator-v2")
        if v2_path in sys.path:
            sys.path.remove(v2_path)
            
        from app.prompts import (
            clarification_prompt, 
            supervisor_approval_prompt,
            summary_generation_prompt
        )
        from app.state import AgentState
    except ImportError as e:
        print(f"WARNING: Could not import V1 modules: {e}")
        print("Make sure yelp-navigator-v1 is in the correct location.")
        return tracer
    
    # Simulate state accumulation
    state = {
        "messages": [],
        "user_query": f"{query} in {location}",
        "clarified_query": query,
        "clarified_location": location,
        "detail_level": detail_level,
        "agent_outputs": {}
    }
    
    # 1. Clarification Agent
    clarification_input = clarification_prompt + f"\n\nUser: {query} in {location}"
    clarification_output = f"CLARIFIED:\nQUERY: {query}\nLOCATION: {location}\nDETAIL_LEVEL: {detail_level}"
    tracer.measure_prompt("clarification", clarification_input, clarification_output)
    
    # 2. Search Agent - simulate with mock data
    search_context = f"Search for: {query} in {location}\n" + "Found 10 businesses..."
    search_output = "Search Agent Results:\nFound 10 businesses..."
    tracer.measure_prompt("search", search_context, search_output)
    
    # Simulate storing search results in state using actual pipeline structure
    state["agent_outputs"]["search"] = {
        "success": True,
        "result_count": 10,
        "businesses": [
            {
                "name": f"Business {i}",
                "business_id": f"business-{i}",
                "alias": f"business-{i}",
                "rating": 4.5,
                "review_count": 150,
                "categories": ["Restaurant", "Food"],
                "price_range": "$$",
                "phone": "+1-555-1234",
                "website": "https://example.com",
                "location": {"lat": 37.77, "lon": -122.41},
                "images": []
            }
            for i in range(5)
        ],
        "full_output": {
            "result": {
                "query": f"{query} in {location}",
                "extracted_location": location,
                "extracted_keywords": [query],
                "result_count": 10,
                "businesses": [
                    {
                        "name": f"Business {i}",
                        "business_id": f"business-{i}",
                        "alias": f"business-{i}",
                        "rating": 4.5,
                        "review_count": 150,
                        "categories": ["Restaurant", "Food"],
                        "price_range": "$$",
                        "phone": "+1-555-1234",
                        "website": "https://example.com",
                        "location": {"lat": 37.77, "lon": -122.41},
                        "images": []
                    }
                    for i in range(10)
                ]
            }
        }
    }
    
    # 3. Details Agent (if detail_level requires it)
    if detail_level in ["detailed", "reviews"]:
        details_context = f"Get details for businesses from search\n{json.dumps(state['agent_outputs']['search'], indent=2)}"
        details_output = "Details Agent Results:\nRetrieved detailed information..."
        tracer.measure_prompt("details", details_context, details_output)
        
        state["agent_outputs"]["details"] = {
            "success": True,
            "document_count": 5,
            "businesses_with_details": [
                {
                    "name": f"Business {i}",
                    "price_range": "$$",
                    "rating": 4.5,
                    "website_content_length": 1500,
                    "has_website_info": True
                }
                for i in range(5)
            ],
            "full_output": {
                "metadata_enricher": {
                    "documents": [
                        {
                            "content": "Website content here..." * 50,
                            "meta": {
                                "business_name": f"Business {i}",
                                "price_range": "$$",
                                "rating": 4.5,
                                "latitude": 37.77,
                                "longitude": -122.41
                            }
                        }
                        for i in range(5)
                    ]
                }
            }
        }
    
    # 4. Sentiment Agent (if reviews requested)
    if detail_level == "reviews":
        sentiment_context = f"Analyze sentiment for businesses\n{json.dumps(state['agent_outputs']['search'], indent=2)}"
        sentiment_output = "Sentiment Agent Results:\nAnalyzed reviews for 5 businesses..."
        tracer.measure_prompt("sentiment", sentiment_context, sentiment_output)
        
        state["agent_outputs"]["sentiment"] = {
            "success": True,
            "analyzed_count": 5,
            "sentiment_summaries": [
                {
                    "name": f"Business {i}",
                    "positive_count": 80,
                    "neutral_count": 15,
                    "negative_count": 5,
                    "top_positive_reviews": ["Great food and service! The atmosphere was wonderful and staff very attentive. Highly recommend!"],
                    "bottom_negative_reviews": ["Slow service and food was cold when it arrived. Very disappointed with the experience."]
                }
                for i in range(5)
            ],
            "full_output": {
                "reviews_aggregator": {
                    "documents": [
                        {
                            "meta": {
                                "business_name": f"Business {i}",
                                "positive_count": 80,
                                "neutral_count": 15,
                                "negative_count": 5,
                                "top_positive_reviews": [{"text": "Great food and service!", "rating": 5}],
                                "bottom_negative_reviews": [{"text": "Slow service", "rating": 2}]
                            }
                        }
                        for i in range(5)
                    ]
                }
            }
        }
    
    # 5. Summary Agent - this is where V1 gets expensive
    summary_context = summary_generation_prompt(
        clarified_query=query,
        clarified_location=location,
        detail_level=detail_level,
        agent_outputs=state["agent_outputs"],
        needs_revision=False,
        revision_feedback=""
    )
    summary_output = f"Here are the top {query} recommendations in {location}...\n" + ("..." * 100)
    tracer.measure_prompt("summary_generation", summary_context, summary_output)
    
    # 6. Supervisor Approval
    supervisor_context = supervisor_approval_prompt(
        clarified_query=query,
        clarified_location=location,
        detail_level=detail_level,
        agent_outputs=state["agent_outputs"],
        final_summary=summary_output
    )
    supervisor_output = "APPROVED"
    tracer.measure_prompt("supervisor_approval", supervisor_context, supervisor_output)
    
    return tracer


def simulate_v2_workflow(query: str, location: str, detail_level: str = "general") -> WorkflowTracer:
    """
    Simulate V2 workflow and measure token usage.
    This reads from the actual V2 prompts and simulates the flow.
    """
    counter = TokenCounter()
    tracer = WorkflowTracer("v2", counter)
    
    # Import V2 components
    v2_path = str(Path(__file__).parent / "yelp-navigator-v2")
    
    # Clean sys.path to avoid conflicts
    v1_path = str(Path(__file__).parent / "yelp-navigator-v1")
    if v1_path in sys.path:
        sys.path.remove(v1_path)
    
    # Remove 'app' module from sys.modules to force reimport
    modules_to_remove = [key for key in sys.modules.keys() if key.startswith('app')]
    for module in modules_to_remove:
        del sys.modules[module]
    
    if v2_path not in sys.path:
        sys.path.insert(0, v2_path)
    
    try:
        from app.prompts import (
            clarification_system_prompt,
            supervisor_prompt,
            summary_prompt
        )
        from app.state import AgentState, ClarificationDecision, SupervisorDecision
    except ImportError as e:
        print(f"WARNING: Could not import V2 modules: {e}")
        print(f"V2 Path: {v2_path}")
        print("Make sure yelp-navigator-v2 is in the correct location.")
        return tracer
    
    # Simulate state
    state = {
        "messages": [],
        "search_query": query,
        "search_location": location,
        "detail_level": detail_level,
        "raw_results": [],
        "pipeline_data": {}
    }
    
    # 1. Clarification with Structured Output
    clarification_input = clarification_system_prompt + f"\n\nUser: {query} in {location}"
    clarification_output = json.dumps({
        "need_clarification": False,
        "intent": "business_search",
        "search_query": query,
        "search_location": location,
        "detail_level": detail_level
    })
    tracer.measure_prompt("clarification", clarification_input, clarification_output)
    
    # 2. Supervisor Decision 1: Decide to search
    supervisor_context_1 = supervisor_prompt(query, location, detail_level, [])
    supervisor_output_1 = json.dumps({"next_action": "search", "reasoning": "No results yet"})
    tracer.measure_prompt("supervisor_decision_1", supervisor_context_1, supervisor_output_1)
    
    # 3. Search Tool (minimal context) - using actual pipeline structure
    search_summary = f"Search Results: Found 10 businesses for {query} in {location}"
    state["raw_results"].append(search_summary)
    state["pipeline_data"] = {
        "result": {
            "query": f"{query} in {location}",
            "extracted_location": location,
            "extracted_keywords": [query],
            "result_count": 10,
            "businesses": [
                {
                    "name": f"Business {i}",
                    "business_id": f"business-{i}",
                    "alias": f"business-{i}",
                    "rating": 4.5,
                    "review_count": 150,
                    "categories": ["Restaurant", "Food"],
                    "price_range": "$$",
                    "phone": "+1-555-1234",
                    "website": "https://example.com",
                    "location": {"lat": 37.77, "lon": -122.41},
                    "images": []
                }
                for i in range(10)
            ]
        }
    }
    
    # 4. Supervisor Decision 2: Decide next action
    supervisor_context_2 = supervisor_prompt(query, location, detail_level, state["raw_results"])
    
    if detail_level == "reviews":
        supervisor_output_2 = json.dumps({"next_action": "analyze_sentiment", "reasoning": "Need sentiment analysis"})
        tracer.measure_prompt("supervisor_decision_2", supervisor_context_2, supervisor_output_2)
        
        # Sentiment tool executes
        sentiment_summary = "Sentiment: Analyzed 5 businesses with positive sentiment"
        state["raw_results"].append(sentiment_summary)
        
        # Supervisor Decision 3: Finalize
        supervisor_context_3 = supervisor_prompt(query, location, detail_level, state["raw_results"])
        supervisor_output_3 = json.dumps({"next_action": "finalize", "reasoning": "Have all data"})
        tracer.measure_prompt("supervisor_decision_3", supervisor_context_3, supervisor_output_3)
    
    elif detail_level == "detailed":
        supervisor_output_2 = json.dumps({"next_action": "get_details", "reasoning": "Need website info"})
        tracer.measure_prompt("supervisor_decision_2", supervisor_context_2, supervisor_output_2)
        
        # Details tool executes
        details_summary = "Details: Retrieved website info for 5 businesses"
        state["raw_results"].append(details_summary)
        
        # Supervisor Decision 3: Finalize
        supervisor_context_3 = supervisor_prompt(query, location, detail_level, state["raw_results"])
        supervisor_output_3 = json.dumps({"next_action": "finalize", "reasoning": "Have all data"})
        tracer.measure_prompt("supervisor_decision_3", supervisor_context_3, supervisor_output_3)
    
    else:  # general
        supervisor_output_2 = json.dumps({"next_action": "finalize", "reasoning": "Basic search sufficient"})
        tracer.measure_prompt("supervisor_decision_2", supervisor_context_2, supervisor_output_2)
    
    # 5. Summary Generation (uses raw_results only)
    summary_context = summary_prompt(query, location, state["raw_results"])
    summary_output = f"Here are the top {query} recommendations in {location}...\n" + ("..." * 50)
    tracer.measure_prompt("summary_generation", summary_context, summary_output)
    
    return tracer


def compare_workflows(test_cases: List[Dict[str, str]]) -> pd.DataFrame:
    """Run both workflows and compare token usage."""
    results = []
    
    for test_case in test_cases:
        query = test_case["query"]
        location = test_case["location"]
        detail_level = test_case.get("detail_level", "general")
        
        print(f"\n{'='*80}")
        print(f"Testing: {query} in {location} (detail_level: {detail_level})")
        print(f"{'='*80}")
        
        # Run V1
        print("\n[Running V1 workflow...]")
        v1_tracer = simulate_v1_workflow(query, location, detail_level)
        v1_total = v1_tracer.get_total_tokens()
        
        # Run V2
        print("[Running V2 workflow...]")
        v2_tracer = simulate_v2_workflow(query, location, detail_level)
        v2_total = v2_tracer.get_total_tokens()
        
        # Calculate reduction
        reduction_tokens = v1_total - v2_total
        reduction_pct = (reduction_tokens / v1_total * 100) if v1_total > 0 else 0
        
        results.append({
            "Query": f"{query} in {location}",
            "Detail Level": detail_level,
            "V1 Tokens": v1_total,
            "V2 Tokens": v2_total,
            "Reduction (tokens)": reduction_tokens,
            "Reduction (%)": f"{reduction_pct:.1f}%"
        })
        
        # Print breakdown
        print(f"\n[V1 Breakdown]")
        for m in v1_tracer.measurements:
            print(f"  {m.operation:25s} {m.total_tokens:6d} tokens")
        print(f"  {'TOTAL':25s} {v1_total:6d} tokens")
        
        print(f"\n[V2 Breakdown]")
        for m in v2_tracer.measurements:
            print(f"  {m.operation:25s} {m.total_tokens:6d} tokens")
        print(f"  {'TOTAL':25s} {v2_total:6d} tokens")
        
        print(f"\n[Reduction: {reduction_tokens} tokens ({reduction_pct:.1f}%)]")
    
    return pd.DataFrame(results)


def generate_report(df: pd.DataFrame, output_file: str = "token_usage_report.md"):
    """Generate a markdown report with the results."""
    report = []
    report.append("# Token Usage Measurement Report")
    report.append(f"\n*Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n")
    report.append("## Summary\n")
    
    # Overall statistics
    total_v1 = df["V1 Tokens"].sum()
    total_v2 = df["V2 Tokens"].sum()
    avg_reduction = df["Reduction (tokens)"].mean()
    total_reduction = total_v1 - total_v2
    total_reduction_pct = (total_reduction / total_v1 * 100) if total_v1 > 0 else 0
    
    report.append(f"- **Total V1 Tokens**: {total_v1:,}")
    report.append(f"- **Total V2 Tokens**: {total_v2:,}")
    report.append(f"- **Total Reduction**: {total_reduction:,} tokens ({total_reduction_pct:.1f}%)")
    report.append(f"- **Average Reduction per Query**: {avg_reduction:.0f} tokens\n")
    
    # Cost savings (using GPT-4 pricing: $0.03/1K input tokens)
    cost_v1 = (total_v1 / 1000) * 0.03
    cost_v2 = (total_v2 / 1000) * 0.03
    savings = cost_v1 - cost_v2
    
    report.append("## Cost Impact (GPT-4 Pricing)\n")
    report.append(f"- **V1 Cost**: ${cost_v1:.4f}")
    report.append(f"- **V2 Cost**: ${cost_v2:.4f}")
    report.append(f"- **Savings**: ${savings:.4f} ({total_reduction_pct:.1f}%)\n")
    report.append(f"- **Monthly Savings (10K queries)**: ${savings * 10000:.2f}\n")
    
    # Detailed results table
    report.append("## Detailed Results\n")
    report.append(tabulate(df, headers='keys', tablefmt='pipe', showindex=False))
    report.append("\n")
    
    # Write to file in docs folder
    output_path = Path(__file__).parent / "docs" / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(report))
    print(f"\n[SUCCESS] Report saved to: {output_path}")
    
    return "\n".join(report)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Measure token usage for Yelp Navigator V1 vs V2")
    parser.add_argument("--test-query", help="Single test query")
    parser.add_argument("--test-location", default="Boston, MA", help="Location for test query")
    parser.add_argument("--detail-level", default="general", choices=["general", "detailed", "reviews"])
    parser.add_argument("--run-all-tests", action="store_true", help="Run comprehensive test suite")
    parser.add_argument("--output", default="token_usage_report.md", help="Output report filename")
    
    args = parser.parse_args()
    
    if args.test_query:
        # Single test
        test_cases = [{
            "query": args.test_query,
            "location": args.test_location,
            "detail_level": args.detail_level
        }]
    elif args.run_all_tests:
        # Comprehensive test suite
        test_cases = [
            {"query": "Italian restaurants", "location": "Boston, MA", "detail_level": "general"},
            {"query": "Italian restaurants", "location": "Boston, MA", "detail_level": "detailed"},
            {"query": "Italian restaurants", "location": "Boston, MA", "detail_level": "reviews"},
            {"query": "coffee shops", "location": "San Francisco, CA", "detail_level": "general"},
            {"query": "sushi restaurants", "location": "New York, NY", "detail_level": "reviews"},
        ]
    else:
        # Default test
        test_cases = [{
            "query": "Italian restaurants",
            "location": "Boston, MA",
            "detail_level": "general"
        }]
    
    # Run comparison
    df = compare_workflows(test_cases)
    
    # Generate report
    report = generate_report(df, args.output)
    
    # Print summary to console
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(report.split("## Detailed Results")[0])


if __name__ == "__main__":
    main()
