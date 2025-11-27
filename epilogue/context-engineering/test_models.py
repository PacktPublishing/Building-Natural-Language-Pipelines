#!/usr/bin/env python3
"""
Systematic testing script for evaluating different LLM models across 
Yelp Navigator versions (v1, v2, v3).

Tests focus on:
- Which nodes were called
- Execution time
- Error handling and recovery
- Model performance characteristics

Does NOT evaluate final response quality (to save API credits).
"""

import json
import time
import sys
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
from langchain_core.messages import HumanMessage

# Test Configuration
MODELS_TO_TEST = [
    {"name": "gpt-oss:20b", "size": "14GB", "context": "128K"},
    {"name": "deepseek-r1:latest", "size": "5.2GB", "context": "128K"},
    {"name": "qwen3:latest", "size": "5.2GB", "context": "40K"},
]

TEST_QUERIES = [
    "best pizza places in Chicago",
    "best pizza places in Chicago and what reviewers said",
    "best pizza places in Chicago and website information",
]

VERSIONS = ["v1", "v2", "v3"]

# Results storage
test_results = []


class NodeTracker:
    """Track which nodes are executed during graph traversal."""
    
    def __init__(self):
        self.nodes_called = []
        self.node_timings = {}
        self.errors = []
        
    def track_event(self, event: Dict[str, Any]):
        """Process a streaming event from the graph."""
        if 'node' in event:
            node_name = event['node']
            
            # Track node execution
            if node_name not in self.nodes_called:
                self.nodes_called.append(node_name)
                self.node_timings[node_name] = 0
            
        # Track errors in metadata
        if 'metadata' in event:
            metadata = event['metadata']
            if isinstance(metadata, dict) and metadata.get('error'):
                self.errors.append({
                    'node': event.get('node', 'unknown'),
                    'error': metadata.get('error'),
                    'timestamp': time.time()
                })


def import_version_graph(version: str, model_name: str):
    """
    Dynamically import and configure the graph for a specific version.
    Sets TEST_MODEL environment variable before importing.
    """
    import os
    import sys
    import importlib
    
    try:
        # Ensure shared module is in path (only need this once)
        shared_path = Path(__file__).parent / "shared"
        if str(shared_path.parent) not in sys.path:
            sys.path.insert(0, str(shared_path.parent))
        
        # Set the TEST_MODEL environment variable BEFORE any imports
        os.environ["TEST_MODEL"] = model_name
        
        # Add version directory to sys.path temporarily
        version_dir = Path(__file__).parent / f"yelp-navigator-{version}"
        if not version_dir.exists():
            print(f"❌ Version directory not found: {version_dir}")
            return None
        
        # Add to path
        sys.path.insert(0, str(version_dir))
        
        try:
            # Clear any cached imports for app modules from previous version
            modules_to_clear = [k for k in list(sys.modules.keys()) if k.startswith('app')]
            for mod in modules_to_clear:
                del sys.modules[mod]
            
            # Import the graph module - this will use relative imports correctly
            import app.graph as graph_module
            
            # Get the graph based on version
            if version == "v1":
                graph = graph_module.build_workflow_graph().compile()
            elif version == "v2":
                graph = graph_module.graph
            elif version == "v3":
                graph = graph_module.graph
            else:
                raise ValueError(f"Unknown version: {version}")
            
            return graph
            
        finally:
            # Always remove from sys.path when done
            if str(version_dir) in sys.path:
                sys.path.remove(str(version_dir))
        
    except Exception as e:
        print(f"❌ Error importing {version} graph: {e}")
        import traceback
        traceback.print_exc()
        return None


class TimeoutException(Exception):
    """Custom exception for timeout."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutException("Test exceeded 2 minute timeout")

def run_test(graph, query: str, version: str, model: str) -> Dict[str, Any]:
    """
    Run a single test query through the graph.
    Times out after 2 minutes.
    
    Returns metrics about execution without evaluating response quality.
    """
    tracker = NodeTracker()
    start_time = time.time()
    
    result = {
        "query": query,
        "version": version,
        "model": model,
        "success": False,
        "total_time": 0,
        "nodes_called": [],
        "node_sequence": [],
        "errors": [],
        "error_recovery": False,
        "final_state_keys": [],
        "timed_out": False,
        "timeout_duration": 120,  # 2 minutes in seconds
    }
    
    try:
        # Set up timeout (2 minutes)
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(120)  # 2 minutes
        
        # Prepare input
        initial_state = {
            "messages": [HumanMessage(content=query)]
        }
        
        # For v1, also set user_query
        if version == "v1":
            initial_state["user_query"] = query
        
        # Stream the graph execution
        node_sequence = []
        final_state = None
        
        for event in graph.stream(initial_state, stream_mode="updates"):
            # Track which node executed
            for node_name, node_data in event.items():
                if node_name != "__start__" and node_name != "__end__":
                    node_sequence.append(node_name)
                    tracker.track_event({"node": node_name})
                    
                    # Store the latest state data
                    final_state = node_data
                    
                    # Check for errors in the node data
                    if isinstance(node_data, dict):
                        if node_data.get("errors") or node_data.get("error"):
                            tracker.errors.append({
                                "node": node_name,
                                "error": node_data.get("errors") or node_data.get("error"),
                                "timestamp": time.time()
                            })
        
        end_time = time.time()
        
        # Cancel the alarm
        signal.alarm(0)
        
        result["success"] = True
        result["total_time"] = end_time - start_time
        result["nodes_called"] = list(set(node_sequence))  # Unique nodes
        result["node_sequence"] = node_sequence  # Full sequence
        result["errors"] = tracker.errors
        result["error_recovery"] = len(tracker.errors) > 0  # Had errors but completed
        
        # Extract final response from state
        if final_state and isinstance(final_state, dict):
            # Try to get the last message or final_response
            if "messages" in final_state and final_state["messages"]:
                last_message = final_state["messages"][-1]
                result["final_response"] = getattr(last_message, "content", str(last_message))
            elif "final_response" in final_state:
                result["final_response"] = final_state["final_response"]
        
    except TimeoutException as e:
        # Test timed out
        signal.alarm(0)  # Cancel the alarm
        end_time = time.time()
        result["success"] = False
        result["timed_out"] = True
        result["total_time"] = end_time - start_time
        result["nodes_called"] = tracker.nodes_called
        result["node_sequence"] = tracker.nodes_called
        result["errors"] = tracker.errors + [{
            "node": "timeout",
            "error": str(e),
            "error_type": "TimeoutException"
        }]
        
    except KeyboardInterrupt:
        signal.alarm(0)  # Cancel the alarm
        raise
    except Exception as e:
        signal.alarm(0)  # Cancel the alarm
        end_time = time.time()
        result["success"] = False
        result["total_time"] = end_time - start_time
        result["nodes_called"] = tracker.nodes_called
        result["node_sequence"] = tracker.nodes_called
        result["errors"] = tracker.errors + [{
            "node": "graph_execution",
            "error": str(e),
            "error_type": type(e).__name__
        }]
    
    return result


def run_all_tests():
    """Run all combinations of models, versions, and queries."""
    print("=" * 80)
    print("🧪 Starting Systematic Model Testing")
    print("=" * 80)
    print(f"\nModels: {len(MODELS_TO_TEST)}")
    print(f"Versions: {len(VERSIONS)}")
    print(f"Queries: {len(TEST_QUERIES)}")
    print(f"Total tests: {len(MODELS_TO_TEST) * len(VERSIONS) * len(TEST_QUERIES)}\n")
    
    test_count = 0
    total_tests = len(MODELS_TO_TEST) * len(VERSIONS) * len(TEST_QUERIES)
    
    for model_info in MODELS_TO_TEST:
        model_name = model_info["name"]
        print(f"\n{'='*80}")
        print(f"📊 Testing Model: {model_name} ({model_info['size']}, {model_info['context']} context)")
        print(f"{'='*80}")
        
        for version in VERSIONS:
            print(f"\n  🔧 Version: {version}")
            
            # Import the graph with the current model
            graph = import_version_graph(version, model_name)
            
            if graph is None:
                print(f"    ⚠️  Skipping {version} - failed to load graph")
                continue
            
            for query in TEST_QUERIES:
                test_count += 1
                print(f"\n    [{test_count}/{total_tests}] Query: '{query[:50]}...'")
                
                # Run the test
                result = run_test(graph, query, version, model_name)
                
                # Display immediate feedback
                if result.get("timed_out"):
                    status = "⏱️"
                    time_str = f"{result['total_time']:.2f}s (TIMEOUT)"
                else:
                    status = "✅" if result["success"] else "❌"
                    time_str = f"{result['total_time']:.2f}s"
                
                nodes_str = " → ".join(result["node_sequence"])
                
                print(f"    {status} Time: {time_str}")
                print(f"       Nodes: {nodes_str}")
                
                if result["errors"]:
                    print(f"       ⚠️  Errors: {len(result['errors'])}")
                    for err in result["errors"][:2]:  # Show first 2 errors
                        print(f"          - {err.get('node', 'unknown')}: {str(err.get('error', 'unknown'))[:60]}")
                
                # Store result
                test_results.append(result)
                
                # Small delay to avoid overwhelming the system
                time.sleep(0.5)
    
    print(f"\n{'='*80}")
    print("✅ Testing Complete!")
    print(f"{'='*80}\n")


def generate_report():
    """Generate a comprehensive report from test results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Only save JSON data, skip Markdown report
    json_file = f"model_test_data_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n📊 Raw data saved: {json_file}")
    
    # Print summary to console instead of Markdown file
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    # Print executive summary table
    print("\n## Executive Summary\n")
    print("| Model | Version | Success Rate | Avg Time | Total Errors | Timeouts |")
    print("|-------|---------|--------------|----------|--------------|----------|")
    
    for model_info in MODELS_TO_TEST:
        model_name = model_info["name"]
        for version in VERSIONS:
            filtered = [r for r in test_results 
                       if r["model"] == model_name and r["version"] == version]
            
            if not filtered:
                continue
            
            success_rate = sum(1 for r in filtered if r["success"]) / len(filtered) * 100
            avg_time = sum(r["total_time"] for r in filtered) / len(filtered)
            total_errors = sum(len(r["errors"]) for r in filtered)
            timeouts = sum(1 for r in filtered if r.get("timed_out", False))
            
            timeout_str = f"{timeouts}" if timeouts > 0 else "0"
            print(f"| {model_name} | {version} | {success_rate:.1f}% | {avg_time:.2f}s | {total_errors} | {timeout_str} |")
    
    # Print node execution summary
    print("\n## Node Execution Patterns\n")
    for query in TEST_QUERIES:
        print(f"\n### Query: '{query}'\n")
        for model_info in MODELS_TO_TEST:
            model_name = model_info["name"]
            for version in VERSIONS:
                query_results = [r for r in test_results 
                               if r["query"] == query and r["model"] == model_name and r["version"] == version]
                
                if query_results:
                    result = query_results[0]
                    nodes = ' → '.join(result['node_sequence']) if result['node_sequence'] else "(none)"
                    if result.get('timed_out'):
                        status = "⏱️ TIMEOUT"
                    else:
                        status = "✅" if result['success'] else "❌"
                    print(f"  {status} [{model_name}] [{version}]: {nodes}")
    
    # Print error summary if any
    total_errors = sum(len(r["errors"]) for r in test_results)
    if total_errors > 0:
        print(f"\n## Errors: {total_errors} total\n")
        for result in test_results:
            if result["errors"]:
                print(f"  [{result['model']}] [{result['version']}] {result['query'][:50]}...")
                for err in result["errors"]:
                    print(f"    - {err.get('node', 'unknown')}: {str(err.get('error', 'unknown'))[:80]}")
    
    print("\n" + "=" * 80)
    
    return json_file


def generate_report_old():
    """Original report generation (kept for reference but not used)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"model_test_report_{timestamp}.md"
    
    with open(report_file, 'w') as f:
        f.write("# Model Performance Test Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Tests:** {len(test_results)}\n\n")
        
        # Overview table
        f.write("## Executive Summary\n\n")
        f.write("| Model | Version | Success Rate | Avg Time | Total Errors |\n")
        f.write("|-------|---------|--------------|----------|-------------|\n")
        
        # Calculate metrics per model/version combo
        for model_info in MODELS_TO_TEST:
            model_name = model_info["name"]
            for version in VERSIONS:
                # Filter results
                filtered = [r for r in test_results 
                           if r["model"] == model_name and r["version"] == version]
                
                if not filtered:
                    continue
                
                success_rate = sum(1 for r in filtered if r["success"]) / len(filtered) * 100
                avg_time = sum(r["total_time"] for r in filtered) / len(filtered)
                total_errors = sum(len(r["errors"]) for r in filtered)
                
                f.write(f"| {model_name} | {version} | {success_rate:.1f}% | {avg_time:.2f}s | {total_errors} |\n")
        
        # Detailed results by model
        f.write("\n## Detailed Results by Model\n\n")
        
        for model_info in MODELS_TO_TEST:
            model_name = model_info["name"]
            f.write(f"### {model_name}\n\n")
            f.write(f"**Specs:** {model_info['size']} model, {model_info['context']} context window\n\n")
            
            for version in VERSIONS:
                f.write(f"#### Version {version}\n\n")
                
                # Filter results for this combo
                filtered = [r for r in test_results 
                           if r["model"] == model_name and r["version"] == version]
                
                if not filtered:
                    f.write("*No tests run for this version*\n\n")
                    continue
                
                for query in TEST_QUERIES:
                    query_results = [r for r in filtered if r["query"] == query]
                    
                    if not query_results:
                        continue
                    
                    result = query_results[0]
                    
                    f.write(f"**Query:** `{query}`\n\n")
                    f.write(f"- **Status:** {'✅ Success' if result['success'] else '❌ Failed'}\n")
                    f.write(f"- **Time:** {result['total_time']:.2f}s\n")
                    f.write(f"- **Nodes Called:** {', '.join(result['nodes_called'])}\n")
                    f.write(f"- **Execution Path:** {' → '.join(result['node_sequence'])}\n")
                    
                    if result['errors']:
                        f.write(f"- **Errors:** {len(result['errors'])}\n")
                        for i, err in enumerate(result['errors'], 1):
                            f.write(f"  {i}. `{err.get('node', 'unknown')}`: {str(err.get('error', 'unknown'))[:100]}\n")
                    
                    f.write("\n")
        
        # Node execution patterns
        f.write("\n## Node Execution Patterns\n\n")
        f.write("Analysis of which nodes were called for each query type:\n\n")
        
        for query in TEST_QUERIES:
            f.write(f"### Query: `{query}`\n\n")
            f.write("| Model | Version | Nodes Called |\n")
            f.write("|-------|---------|-------------|\n")
            
            for model_info in MODELS_TO_TEST:
                model_name = model_info["name"]
                for version in VERSIONS:
                    query_results = [r for r in test_results 
                                   if r["query"] == query and r["model"] == model_name and r["version"] == version]
                    
                    if query_results:
                        result = query_results[0]
                        nodes = ' → '.join(result['node_sequence'])
                        f.write(f"| {model_name} | {version} | {nodes} |\n")
            
            f.write("\n")
        
        # Performance comparison
        f.write("\n## Performance Comparison\n\n")
        f.write("### Average Execution Time by Version\n\n")
        
        # Build dynamic header based on versions tested
        versions_tested = sorted(set(r["version"] for r in test_results))
        if not versions_tested:
            f.write("*No test results available*\n\n")
        else:
            header = "| Model | " + " | ".join(versions_tested) + " |\n"
            separator = "|-------|" + "|".join(["----"] * len(versions_tested)) + "|\n"
            f.write(header)
            f.write(separator)
            
            for model_info in MODELS_TO_TEST:
                model_name = model_info["name"]
                times = []
                
                for version in versions_tested:
                    filtered = [r for r in test_results 
                               if r["model"] == model_name and r["version"] == version]
                    
                    if filtered:
                        avg_time = sum(r["total_time"] for r in filtered) / len(filtered)
                        times.append(f"{avg_time:.2f}s")
                    else:
                        times.append("N/A")
                
                row = f"| {model_name} | " + " | ".join(times) + " |\n"
                f.write(row)
        
        # Error analysis
        f.write("\n## Error Analysis\n\n")
        
        total_errors = sum(len(r["errors"]) for r in test_results)
        f.write(f"**Total Errors Encountered:** {total_errors}\n\n")
        
        if total_errors > 0:
            f.write("### Error Breakdown\n\n")
            
            # Collect all errors
            all_errors = []
            for result in test_results:
                for err in result["errors"]:
                    all_errors.append({
                        "model": result["model"],
                        "version": result["version"],
                        "query": result["query"],
                        "node": err.get("node", "unknown"),
                        "error": str(err.get("error", "unknown"))
                    })
            
            # Group by error type
            error_types = {}
            for err in all_errors:
                error_msg = err["error"][:100]
                if error_msg not in error_types:
                    error_types[error_msg] = []
                error_types[error_msg].append(err)
            
            for error_msg, occurrences in error_types.items():
                f.write(f"**Error:** `{error_msg}`\n")
                f.write(f"- Occurrences: {len(occurrences)}\n")
                f.write(f"- Models affected: {', '.join(set(e['model'] for e in occurrences))}\n")
                f.write(f"- Versions affected: {', '.join(set(e['version'] for e in occurrences))}\n\n")
        else:
            f.write("*No errors encountered during testing* ✅\n\n")
        
        # Recommendations
        f.write("\n## Recommendations\n\n")
        
        # Find best performing model
        model_scores = {}
        for model_info in MODELS_TO_TEST:
            model_name = model_info["name"]
            filtered = [r for r in test_results if r["model"] == model_name]
            
            if filtered:
                success_rate = sum(1 for r in filtered if r["success"]) / len(filtered)
                avg_time = sum(r["total_time"] for r in filtered) / len(filtered)
                error_count = sum(len(r["errors"]) for r in filtered)
                
                # Score: success rate - time penalty - error penalty
                score = (success_rate * 100) - (avg_time * 2) - (error_count * 5)
                model_scores[model_name] = score
        
        if model_scores:
            best_model = max(model_scores, key=model_scores.get)
            f.write(f"### Best Overall Model: **{best_model}**\n\n")
            
            f.write("Based on:\n")
            f.write("- Success rate\n")
            f.write("- Average execution time\n")
            f.write("- Error frequency\n\n")
        else:
            f.write("### Best Overall Model: **N/A**\n\n")
            f.write("*No successful tests to evaluate*\n\n")
        
        # Version-specific recommendations
        f.write("### Version-Specific Performance\n\n")
        for version in VERSIONS:
            filtered = [r for r in test_results if r["version"] == version]
            
            if filtered:
                avg_time = sum(r["total_time"] for r in filtered) / len(filtered)
                success_rate = sum(1 for r in filtered if r["success"]) / len(filtered) * 100
                
                f.write(f"**{version.upper()}:**\n")
                f.write(f"- Average time: {avg_time:.2f}s\n")
                f.write(f"- Success rate: {success_rate:.1f}%\n\n")
    
    print(f"\n📄 Report generated: {report_file}")
    
    # Also save raw JSON data
    json_file = f"model_test_data_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"📊 Raw data saved: {json_file}")
    
    return report_file


def main():
    """Main execution function."""
    try:
        # Run all tests
        run_all_tests()
        
        # Generate report
        json_file = generate_report()
        
        print("\n" + "="*80)
        print("🎉 Testing Complete!")
        print("="*80)
        print(f"\nJSON data available in: {json_file}")
        print("\nQuick Summary:")
        
        # Print quick stats
        total_tests = len(test_results)
        successful = sum(1 for r in test_results if r["success"])
        failed = total_tests - successful
        timeouts = sum(1 for r in test_results if r.get("timed_out", False))
        avg_time = sum(r["total_time"] for r in test_results) / total_tests if test_results else 0
        
        print(f"  Total Tests: {total_tests}")
        if total_tests > 0:
            print(f"  Successful: {successful} ({successful/total_tests*100:.1f}%)")
            print(f"  Failed: {failed} ({failed/total_tests*100:.1f}%)")
            print(f"  Timeouts: {timeouts} ({timeouts/total_tests*100:.1f}%)")
            print(f"  Average Time: {avg_time:.2f}s")
        else:
            print(f"  No tests completed successfully")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        if test_results:
            print("Generating partial report...")
            generate_report()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        
        if test_results:
            print("\nGenerating partial report from completed tests...")
            generate_report()


if __name__ == "__main__":
    main()
