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

Architecture:
- Uses subprocess-based execution for process isolation
- Supports concurrent test execution via ThreadPoolExecutor
- Cross-platform compatible (no signal handling)
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Test Configuration
MODELS_TO_TEST = [
    {"name": "gpt-oss:20b", "size": "14GB", "context": "128K"},
    {"name": "deepseek-r1:latest", "size": "5.2GB", "context": "128K"},
    {"name": "qwen3:latest", "size": "5.2GB", "context": "40K"},
    {"name": "gpt-4o-mini", "size": "cloud", "context": "128K"}
]

TEST_QUERIES = [
    "best pizza places in Chicago",
    "best pizza places in Chicago and what reviewers said",
    "best pizza places in Chicago and website information",
]

VERSIONS = ["v1", "v2", "v3"]

# Execution configuration
MAX_WORKERS = 1  # WARNING: High values may consume the timeout budget quickly if using Ollama
TEST_TIMEOUT = 120  # Timeout in seconds (2 minutes)
TEST_TEMPERATURE = "0.0"  # Temperature setting for models

# Results storage
test_results = []


def run_test_in_process(model: str, version: str, query: str) -> Dict[str, Any]:
    """
    Spawns a pristine subprocess for one test case.
    
    This approach ensures:
    - Clean import state for each test
    - No singleton pollution between versions
    - Cross-platform timeout handling
    - Ability to run tests in parallel
    - Progress tracking for timeout recovery
    
    Args:
        model: Model name to test
        version: Graph version (v1, v2, v3)
        query: Test query string
    
    Returns:
        Dictionary with test results or error information
    """
    worker_script = Path(__file__).parent / "run_single_test_worker.py"
    
    if not worker_script.exists():
        return {
            "success": False,
            "error": f"Worker script not found: {worker_script}",
            "model": model,
            "version": version,
            "query": query,
            "timed_out": False
        }
    
    # Create a temporary file for progress tracking
    progress_fd, progress_file = tempfile.mkstemp(suffix=".json", prefix="test_progress_")
    os.close(progress_fd)  # Close the file descriptor, worker will write to path
    
    try:
        cmd = [
            sys.executable,
            str(worker_script),
            "--model", model,
            "--version", version,
            "--query", query,
            "--temperature", TEST_TEMPERATURE,
            "--progress-file", progress_file
        ]
        # Run with timeout - handles this safely across platforms
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TEST_TIMEOUT
        )
        
        worker_logs = ""
        json_data = {}
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr or "Process failed with non-zero exit code",
                "model": model,
                "version": version,
                "query": query,
                "timed_out": False,
                "returncode": result.returncode
            }
        
        try:
            stdout = result.stdout
            # Split by marker and take the last part
            if "___JSON_RESULT_START___" in stdout:
                parts = stdout.split("___JSON_RESULT_START___")
                worker_logs = parts[0].strip()  
                json_str = parts[-1].strip()
            else:
                # Fallback: Try to find the last line (risky but better than nothing)
                lines = stdout.strip().split('\n')
                json_str = lines[-1] if lines else "{}"
                worker_logs = "\n".join(lines[:-1])

            json_data = json.loads(json_str)

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse worker output: {e}",
                "model": model,
                "version": version,
                "query": query,
                "timed_out": True,
                "timeout_duration": TEST_TIMEOUT,
                "nodes_called": [],
                "node_sequence": [],
                "errors": [{"node": "timeout", "error": "TimeoutExpired", "error_type": "TimeoutExpired"}]
            }
    
        json_data["worker_logs"] = worker_logs
        return json_data

    except subprocess.TimeoutExpired:
        # Try to recover partial results from progress file
        partial_result = {
            "success": False,
            "error": f"Test exceeded {TEST_TIMEOUT}s timeout",
            "model": model,
            "version": version,
            "query": query,
            "timed_out": True,
            "timeout_duration": TEST_TIMEOUT,
            "nodes_called": [],
            "node_sequence": [],
            "node_outputs": [],
            "current_node": None,
            "current_node_start_time": None,
            "timeout_info": "No progress file recovered",
            "errors": [{"node": "timeout", "error": "TimeoutExpired", "error_type": "TimeoutExpired"}]
        }
        
        # Attempt to read progress file
        try:
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    saved_progress = json.load(f)
                    # Merge saved progress into result
                    partial_result["nodes_called"] = saved_progress.get("nodes_called", [])
                    partial_result["node_sequence"] = saved_progress.get("node_sequence", [])
                    partial_result["node_outputs"] = saved_progress.get("node_outputs", [])
                    partial_result["total_time"] = saved_progress.get("total_time", TEST_TIMEOUT)
                    
                    # Critical: capture what node was running when timeout occurred
                    current_node = saved_progress.get("current_node")
                    current_node_start = saved_progress.get("current_node_start_time")
                    
                    if current_node:
                        partial_result["current_node"] = current_node
                        partial_result["current_node_start_time"] = current_node_start
                        elapsed_in_node = TEST_TIMEOUT - (current_node_start or 0)
                        partial_result["timeout_info"] = f"Timed out while executing '{current_node}' (running for {elapsed_in_node:.1f}s)"
                        # Add timeout error with context
                        partial_result["errors"] = [{
                            "node": current_node,
                            "error": f"TimeoutExpired after {elapsed_in_node:.1f}s in this node",
                            "error_type": "TimeoutExpired"
                        }]
                    else:
                        partial_result["timeout_info"] = "Timed out between nodes or during initialization"
                    
                    if saved_progress.get("errors"):
                        partial_result["errors"].extend(saved_progress["errors"])
        except Exception as e:
            partial_result["progress_recovery_error"] = str(e)
        finally:
            # Clean up progress file
            try:
                os.unlink(progress_file)
            except Exception:
                pass
        
        return partial_result
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "model": model,
            "version": version,
            "query": query,
            "timed_out": False,
            "error_type": type(e).__name__
        }
    finally:
        # Always clean up progress file
        try:
            if os.path.exists(progress_file):
                os.unlink(progress_file)
        except Exception:
            pass


def run_all_tests(models=None, versions=None, queries=None):
    """
    Run all combinations of models, versions, and queries.
    
    Args:
        models: List of model dicts to test. If None, uses MODELS_TO_TEST.
        versions: List of version strings to test. If None, uses VERSIONS.
        queries: List of query strings to test. If None, uses TEST_QUERIES.
    
    Uses ThreadPoolExecutor to run tests concurrently, dramatically
    reducing execution time for I/O-bound LLM testing.
    """
    # Use provided parameters or fall back to global defaults
    models_to_test = models if models is not None else MODELS_TO_TEST
    versions_to_test = versions if versions is not None else VERSIONS
    queries_to_test = queries if queries is not None else TEST_QUERIES
    
    print("=" * 80)
    print("Starting Systematic Model Testing")
    print("=" * 80)
    print(f"\nModels: {len(models_to_test)}")
    print(f"Versions: {len(versions_to_test)}")
    print(f"Queries: {len(queries_to_test)}")
    total_tests = len(models_to_test) * len(versions_to_test) * len(queries_to_test)
    print(f"Total tests: {total_tests}")
    print(f"Max concurrent workers: {MAX_WORKERS}")
    print(f"Timeout per test: {TEST_TIMEOUT}s")
    print(f"Temperature: {TEST_TEMPERATURE}\n")
    
    # Build list of all test tasks
    tasks = []
    for model_info in models_to_test:
        for version in versions_to_test:
            for query in queries_to_test:
                tasks.append({
                    "model": model_info["name"],
                    "model_info": model_info,
                    "version": version,
                    "query": query
                })
    
    # Run tests concurrently
    completed_count = 0
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(
                run_test_in_process,
                task["model"],
                task["version"],
                task["query"]
            ): task
            for task in tasks
        }
        
        # Process results as they complete
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            completed_count += 1
            
            try:
                result = future.result()
                
                # Display immediate feedback
                model_name = task["model"]
                version = task["version"]
                query = task["query"]
                
                if result.get("timed_out"):
                    status = "[TIMEOUT]"
                    time_str = f"{result.get('total_time', TEST_TIMEOUT):.2f}s"
                else:
                    status = "[OK]" if result.get("success") else "[FAIL]"
                    time_str = f"{result.get('total_time', 0):.2f}s"
                
                nodes_str = " -> ".join(result.get("node_sequence", []))
                
                # Add current_node indicator for timeouts
                if result.get("current_node"):
                    nodes_str += f" -> [{result['current_node']}] TIMEOUT HERE"
                
                print(f"[{completed_count}/{total_tests}] {status} {model_name} | {version} | {query[:40]}...")
                print(f"  Time: {time_str} | Nodes: {nodes_str}")
                
                if result.get("timeout_info"):
                    print(f"  {result['timeout_info']}")
                
                if result.get("errors"):
                    print(f"  Errors: {len(result['errors'])}")
                    for err in result["errors"][:2]:  # Show first 2 errors
                        print(f"    - {err.get('node', 'unknown')}: {str(err.get('error', 'unknown'))[:60]}")
                
                # Store result
                test_results.append(result)
                
            except Exception as e:
                print(f"[{completed_count}/{total_tests}] [ERROR] Failed to process result: {e}")
                # Store error result
                test_results.append({
                    "success": False,
                    "error": str(e),
                    "model": task["model"],
                    "version": task["version"],
                    "query": task["query"]
                })
    
    elapsed_time = time.time() - start_time
    print(f"\n{'='*80}")
    print("Testing Complete!")
    print(f"Total time: {elapsed_time:.2f}s ({elapsed_time/60:.1f} minutes)")
    print(f"Average time per test: {elapsed_time/total_tests:.2f}s")
    print(f"{'='*80}\n")


def generate_report():
    """
    Generate a comprehensive report from test results using pandas.
    
    Exports data to multiple formats:
    - JSON (raw data)
    - CSV (summary statistics)
    - Console output (markdown tables)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw JSON data
    json_file = f"model_test_data_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nRaw data saved: {json_file}")
    
    # Use pandas for analysis if available
    try:
        import pandas as pd
        
        # Convert results to DataFrame
        df = pd.DataFrame(test_results)
        
        # Ensure required columns exist
        if 'total_time' not in df.columns:
            df['total_time'] = 0
        if 'timed_out' not in df.columns:
            df['timed_out'] = False
        
        # Calculate error counts
        df['error_count'] = df['errors'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        
        # Print summary to console
        print("\n" + "=" * 80)
        print("TEST SUMMARY (via Pandas)")
        print("=" * 80)
        
        # Executive Summary
        print("\n## Executive Summary\n")
        summary = df.groupby(['model', 'version']).agg({
            'success': ['mean', 'count'],
            'total_time': 'mean',
            'error_count': 'sum',
            'timed_out': 'sum'
        }).round(2)
        
        # Flatten column names
        summary.columns = ['success_rate', 'test_count', 'avg_time', 'total_errors', 'timeouts']
        summary['success_rate'] = (summary['success_rate'] * 100).round(1)
        
        # Display as markdown table
        print(summary.to_markdown())
        
        # Save summary to CSV
        csv_file = f"model_test_summary_{timestamp}.csv"
        summary.to_csv(csv_file)
        print(f"\nSummary statistics saved: {csv_file}")
        
        # Node Execution Patterns
        print("\n## Node Execution Patterns\n")
        for query in TEST_QUERIES:
            print(f"\n### Query: '{query}'\n")
            query_df = df[df['query'] == query]
            
            for _, row in query_df.iterrows():
                nodes = ' -> '.join(row.get('node_sequence', [])) if row.get('node_sequence') else "(none)"
                if row.get('timed_out'):
                    status = "[TIMEOUT]"
                else:
                    status = "[OK]" if row.get('success') else "[FAIL]"
                print(f"  {status} [{row['model']}] [{row['version']}]: {nodes}")
        
        # Error Summary
        total_errors = df['error_count'].sum()
        if total_errors > 0:
            print(f"\n## Errors: {int(total_errors)} total\n")
            error_df = df[df['error_count'] > 0]
            
            for _, row in error_df.iterrows():
                print(f"  [{row['model']}] [{row['version']}] {row['query'][:50]}...")
                for err in row['errors']:
                    print(f"    - {err.get('node', 'unknown')}: {str(err.get('error', 'unknown'))[:80]}")
        
        print("\n" + "=" * 80)
        
        return json_file, csv_file
    
    except ImportError:
        # Fallback to manual reporting if pandas not available
        print("\nNote: Install pandas for enhanced reporting (pip install pandas)")
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        # Manual summary table
        print("\n## Executive Summary\n")
        print("| Model | Version | Success Rate | Avg Time | Total Errors | Timeouts |")
        print("|-------|---------|--------------|----------|--------------|----------|")
        
        for model_info in MODELS_TO_TEST:
            model_name = model_info["name"]
            for version in VERSIONS:
                filtered = [r for r in test_results 
                           if r.get("model") == model_name and r.get("version") == version]
                
                if not filtered:
                    continue
                
                success_rate = sum(1 for r in filtered if r.get("success")) / len(filtered) * 100
                avg_time = sum(r.get("total_time", 0) for r in filtered) / len(filtered)
                total_errors = sum(len(r.get("errors", [])) for r in filtered)
                timeouts = sum(1 for r in filtered if r.get("timed_out", False))
                
                print(f"| {model_name} | {version} | {success_rate:.1f}% | {avg_time:.2f}s | {total_errors} | {timeouts} |")
        
        print("\n" + "=" * 80)
        
        return json_file


def parse_arguments():
    """
    Parse command-line arguments for fine-grained test control.
    
    Allows users to run specific test subsets without editing code.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Systematic testing for LLM models across LangGraph versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python stress_test_architectures.py
  
  # Test only specific model
  python stress_test_architectures.py --only-model "gpt-oss:20b"
  
  # Test specific version
  python stress_test_architectures.py --only-version v2
  
  # Test with custom query
  python stress_test_architectures.py --only-query "best pizza in Chicago"
  
  # Reduce timeout for faster testing
  python stress_test_architectures.py --timeout 60
  
  # Increase parallelism
  python stress_test_architectures.py --max-workers 10
        """
    )
    
    parser.add_argument(
        "--only-model",
        type=str,
        help="Test only the specified model (e.g., 'gpt-oss:20b')"
    )
    
    parser.add_argument(
        "--only-version",
        type=str,
        choices=["v1", "v2", "v3"],
        help="Test only the specified version"
    )
    
    parser.add_argument(
        "--only-query",
        type=str,
        help="Test only the specified query (exact match)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=TEST_TIMEOUT,
        help=f"Timeout per test in seconds (default: {TEST_TIMEOUT})"
    )
    
    parser.add_argument(
        "--temperature",
        type=str,
        default=TEST_TEMPERATURE,
        help=f"Temperature setting for models (default: {TEST_TEMPERATURE})"
    )
    
    parser.add_argument(
        "--list-options",
        action="store_true",
        help="List all available models, versions, and queries"
    )
    
    parser.add_argument(
        "--max-workers",
        type=int,
        default=MAX_WORKERS,
        help=f"Number of parallel test executions (default: {MAX_WORKERS})"
    )
    
    return parser.parse_args()


def main():
    """Main execution function with CLI argument support."""
    global MAX_WORKERS, TEST_TIMEOUT, TEST_TEMPERATURE
    
    # Parse arguments
    args = parse_arguments()
    
    # Handle --list-options
    if args.list_options:
        print("Available Models:")
        for model in MODELS_TO_TEST:
            print(f"  - {model['name']} ({model['size']}, {model['context']} context)")
        
        print("\nAvailable Versions:")
        for version in VERSIONS:
            print(f"  - {version}")
        
        print("\nAvailable Queries:")
        for query in TEST_QUERIES:
            print(f"  - {query}")
        
        return
    
    # Apply CLI overrides
    MAX_WORKERS = args.max_workers
    TEST_TIMEOUT = args.timeout
    TEST_TEMPERATURE = args.temperature
    
    # Filter test configuration based on arguments
    models_to_test = MODELS_TO_TEST
    versions_to_test = VERSIONS
    queries_to_test = TEST_QUERIES
    
    if args.only_model:
        models_to_test = [m for m in MODELS_TO_TEST if m["name"] == args.only_model]
        if not models_to_test:
            print(f"Error: Model '{args.only_model}' not found.")
            print("Use --list-options to see available models.")
            return
    
    if args.only_version:
        versions_to_test = [args.only_version]
    
    if args.only_query:
        queries_to_test = [q for q in TEST_QUERIES if q == args.only_query]
        if not queries_to_test:
            print(f"Error: Query '{args.only_query}' not found.")
            print("Use --list-options to see available queries.")
            return
    
    try:
        # Run filtered tests by passing parameters
        run_all_tests(models=models_to_test, versions=versions_to_test, queries=queries_to_test)
        
        # Generate report
        report_files = generate_report()
        
        print("\n" + "="*80)
        print("Testing Complete!")
        print("="*80)
        
        if isinstance(report_files, tuple):
            json_file, csv_file = report_files
            print(f"\nJSON data: {json_file}")
            print(f"CSV summary: {csv_file}")
        else:
            print(f"\nJSON data: {report_files}")
        
        print("\nQuick Summary:")
        
        # Print quick stats
        total_tests = len(test_results)
        successful = sum(1 for r in test_results if r.get("success"))
        failed = total_tests - successful
        timeouts = sum(1 for r in test_results if r.get("timed_out", False))
        avg_time = sum(r.get("total_time", 0) for r in test_results) / total_tests if test_results else 0
        
        print(f"  Total Tests: {total_tests}")
        if total_tests > 0:
            print(f"  Successful: {successful} ({successful/total_tests*100:.1f}%)")
            print(f"  Failed: {failed} ({failed/total_tests*100:.1f}%)")
            print(f"  Timeouts: {timeouts} ({timeouts/total_tests*100:.1f}%)")
            print(f"  Average Time: {avg_time:.2f}s")
        else:
            print(f"  No tests completed successfully")
        
    except KeyboardInterrupt:
        print("\n\nWARNING: Testing interrupted by user")
        if test_results:
            print("Generating partial report...")
            generate_report()
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        
        if test_results:
            print("\nGenerating partial report from completed tests...")
            generate_report()


if __name__ == "__main__":
    main()
