#!/usr/bin/env python3
"""
Worker script that runs a single test in complete process isolation.
Accepts CLI arguments, imports the appropriate graph version, runs the test,
and outputs JSON results to stdout.

This ensures clean import state and prevents module pollution between tests.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

from langchain_core.messages import HumanMessage


# Input adapters for different graph versions
# Decouples version-specific input logic from execution
INPUT_MAPPERS = {
    "v1": lambda query: {
        "messages": [HumanMessage(content=query)],
        "user_query": query  # v1 requires both messages and user_query
    },
    "v2": lambda query: {
        "messages": [HumanMessage(content=query)]
    },
    "v3": lambda query: {
        "messages": [HumanMessage(content=query)]
    }
}


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


def run_single_test(version: str, model: str, query: str, temperature: str = "0.0", progress_file: str = None) -> Dict[str, Any]:
    """
    Run a single test in isolation.
    
    Args:
        version: Graph version (v1, v2, v3)
        model: Model name to test
        query: Test query string
        temperature: Temperature setting for the model
        progress_file: Optional path to file for writing incremental progress
    
    Returns:
        Dictionary with test results
    """
    result = {
        "query": query,
        "version": version,
        "model": model,
        "temperature": temperature,
        "success": False,
        "total_time": 0,
        "nodes_called": [],
        "node_sequence": [],
        "errors": [],
        "error_recovery": False,
        "last_two_messages": [],
        "node_outputs": [],
        "current_node": None,  # Track which node is currently executing
        "current_node_start_time": None,
    }
    
    tracker = NodeTracker()
    start_time = time.time()
    
    def save_progress():
        """Save current progress to file for timeout recovery."""
        if progress_file:
            try:
                with open(progress_file, 'w') as f:
                    json.dump(result, f)
            except Exception:
                pass  # Don't fail the test if we can't write progress
    
    try:
        # Set environment variables for this process
        os.environ["TEST_MODEL"] = model
        os.environ["TEST_TEMPERATURE"] = temperature
        
        # Add version directory to path
        version_dir = Path(__file__).parent / f"yelp-navigator-{version}"
        if not version_dir.exists():
            raise FileNotFoundError(f"Version directory not found: {version_dir}")
        
        sys.path.insert(0, str(version_dir))
        
        # Import the graph module
        import app.graph as graph_module
        graph = graph_module.graph
        
        # Prepare input using version-specific mapper
        mapper = INPUT_MAPPERS.get(version)
        if not mapper:
            raise ValueError(f"No input mapper defined for version: {version}")
        
        initial_state = mapper(query)
        
        # Stream the graph execution
        node_sequence = []
        node_outputs = []
        final_state = None
        
        for event in graph.stream(initial_state, stream_mode="updates"):
            # Track which node executed
            for node_name, node_data in event.items():
                if node_name != "__start__" and node_name != "__end__":
                    # Mark this node as currently executing BEFORE processing
                    result["current_node"] = node_name
                    result["current_node_start_time"] = time.time() - start_time
                    save_progress()  # Save immediately so timeout knows what's running
                    
                    node_sequence.append(node_name)
                    tracker.track_event({"node": node_name})
                    
                    # Store the latest state data
                    final_state = node_data
                    
                    # Capture what the node said/output
                    node_output = {
                        "node": node_name,
                        "timestamp": time.time() - start_time,
                    }
                    
                    # Update result immediately for timeout recovery
                    result["nodes_called"] = list(set(node_sequence))
                    result["node_sequence"] = node_sequence
                    result["total_time"] = time.time() - start_time
                    
                    # Robust type checking for node_data
                    # LangGraph can return dict, Command objects, or other state update types
                    if isinstance(node_data, dict):
                        # Extract messages if available
                        if "messages" in node_data and node_data["messages"]:
                            # Get the last message from this node's output
                            last_msg = node_data["messages"][-1]
                            node_output["message_type"] = type(last_msg).__name__
                            node_output["content"] = getattr(last_msg, "content", str(last_msg))[:500]
                        
                        # Also capture any other relevant fields
                        if "next_action" in node_data:
                            node_output["next_action"] = node_data["next_action"]
                        if "tool_calls" in node_data:
                            node_output["tool_calls"] = str(node_data["tool_calls"])[:200]
                        
                        # Check for errors in the node data
                        if node_data.get("errors") or node_data.get("error"):
                            node_output["error"] = str(node_data.get("errors") or node_data.get("error"))[:200]
                            tracker.errors.append({
                                "node": node_name,
                                "error": node_data.get("errors") or node_data.get("error"),
                                "timestamp": time.time()
                            })
                    else:
                        # Handle non-dict node_data (e.g., Command objects)
                        node_output["data_type"] = type(node_data).__name__
                        node_output["data_repr"] = str(node_data)[:500]
                    
                    node_outputs.append(node_output)
                    result["node_outputs"] = node_outputs
                    
                    # Clear current_node since this node has completed
                    result["current_node"] = None
                    result["current_node_start_time"] = None
                    
                    # Save progress after each node completes
                    save_progress()
        
        end_time = time.time()
        
        result["success"] = True
        result["total_time"] = end_time - start_time
        result["nodes_called"] = list(set(node_sequence))
        result["node_sequence"] = node_sequence
        result["node_outputs"] = node_outputs
        result["errors"] = tracker.errors
        result["error_recovery"] = len(tracker.errors) > 0
        
        # Extract final response from state
        if final_state and isinstance(final_state, dict):
            if "messages" in final_state and final_state["messages"]:
                last_message = final_state["messages"][-1]
                result["final_response"] = getattr(last_message, "content", str(last_message))
                
                # Track last two messages
                messages = final_state["messages"]
                if len(messages) >= 2:
                    result["last_two_messages"] = [
                        {
                            "type": type(messages[-2]).__name__,
                            "content": getattr(messages[-2], "content", str(messages[-2]))
                        },
                        {
                            "type": type(messages[-1]).__name__,
                            "content": getattr(messages[-1], "content", str(messages[-1]))
                        }
                    ]
                elif len(messages) == 1:
                    result["last_two_messages"] = [
                        {
                            "type": type(messages[-1]).__name__,
                            "content": getattr(messages[-1], "content", str(messages[-1]))
                        }
                    ]
            elif "final_response" in final_state:
                result["final_response"] = final_state["final_response"]
        
    except Exception as e:
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


def main():
    """Main entry point for the worker script."""
    parser = argparse.ArgumentParser(description="Run a single test in isolation")
    parser.add_argument("--version", required=True, help="Graph version (v1, v2, v3)")
    parser.add_argument("--model", required=True, help="Model name to test")
    parser.add_argument("--query", required=True, help="Test query string")
    parser.add_argument("--temperature", default="0.0", help="Temperature setting")
    parser.add_argument("--progress-file", help="File path for writing incremental progress")
    
    args = parser.parse_args()
    
    # Run the test
    result = run_single_test(
        version=args.version,
        model=args.model,
        query=args.query,
        temperature=args.temperature,
        progress_file=args.progress_file
    )
    
    # Output JSON to stdout for the parent process to read
    print(json.dumps(result))


if __name__ == "__main__":
    main()
