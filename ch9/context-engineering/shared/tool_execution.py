"""
Unified tool execution logic for V1, V2, and V3 of yelp-navigator.

This module provides a shared function for executing tools with optional error tracking
and metadata collection, eliminating code duplication across versions.
"""

from typing import Dict, Any, Callable
from datetime import datetime
import time


def execute_tool_with_tracking(
    tool_func: Callable,
    tool_name: str,
    tool_args: Dict[str, Any],
    state: Dict[str, Any],
    track_errors: bool = False,
    add_metadata: bool = False
) -> Dict[str, Any]:
    """
    Unified tool execution with optional error tracking and metadata.
    
    This function provides a consistent interface for executing tools (search, details, 
    sentiment) across all versions of the yelp-navigator application. It handles:
    - Tool invocation with arguments
    - Result storage in agent_outputs
    - Optional error tracking (retry counts, consecutive failures)
    - Optional metadata (execution time, timestamps)
    - Pipeline data storage for downstream nodes
    
    Args:
        tool_func: The tool function to call (e.g., search_businesses, get_business_details)
        tool_name: Name for tracking (e.g., "search", "details", "sentiment")
        tool_args: Arguments to pass to the tool function
        state: Current agent state dictionary
        track_errors: Whether to track retry/failure counts (V3 feature)
        add_metadata: Whether to add execution metadata (V3 feature)
    
    Returns:
        Dict with keys to update in state:
        - agent_outputs: Updated with tool result
        - pipeline_data: For search tool, stores full_output
        - total_error_count: Incremented on failure (if track_errors=True)
        - consecutive_failures: Updated per-tool failure counts (if track_errors=True)
        - retry_counts: Updated per-tool retry counts (if track_errors=True)
        - last_node_executed: Name of the node that executed (if track_errors=True)
        - metadata: Execution timing and context (if add_metadata=True and in result)
    
    Example:
        # V1 usage (minimal):
        update = execute_tool_with_tracking(
            tool_func=search_businesses,
            tool_name="search",
            tool_args={"query": "pizza in San Francisco"},
            state=state,
            track_errors=False,
            add_metadata=False
        )
        
        # V3 usage (full features):
        update = execute_tool_with_tracking(
            tool_func=search_businesses,
            tool_name="search",
            tool_args={"query": "pizza in San Francisco"},
            state=state,
            track_errors=True,
            add_metadata=True
        )
    """
    start_time = time.time() if add_metadata else None
    
    try:
        # Execute the tool
        result = tool_func.invoke(tool_args)
        execution_time = time.time() - start_time if add_metadata else None
        
        # Add metadata if requested (for both success and failure)
        if add_metadata:
            result['metadata'] = {
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': datetime.now().isoformat(),
            }
            if result.get("success"):
                result['metadata']['retry_count'] = state.get("retry_counts", {}).get(tool_name, 0)
        
        # Update agent outputs with the result
        agent_outputs = state.get('agent_outputs', {}).copy()
        agent_outputs[tool_name] = result
        
        update_dict = {"agent_outputs": agent_outputs}
        
        # Track errors if requested
        if track_errors:
            consecutive_failures = state.get('consecutive_failures', {}).copy()
            if result.get("success"):
                # Reset consecutive failures on success
                consecutive_failures[tool_name] = 0
            else:
                # Increment consecutive failures and total error count
                consecutive_failures[tool_name] = consecutive_failures.get(tool_name, 0) + 1
                update_dict["total_error_count"] = state.get("total_error_count", 0) + 1
            
            update_dict["consecutive_failures"] = consecutive_failures
            update_dict["last_node_executed"] = f"{tool_name}_tool"
        
        # Store pipeline data for search tool (used by downstream nodes)
        if tool_name == "search" and result.get("success"):
            update_dict["pipeline_data"] = result.get('full_output', {})
        
        return update_dict
        
    except Exception as e:
        # Handle exceptions during tool execution
        execution_time = time.time() - start_time if add_metadata else None
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }
        
        if add_metadata:
            error_result['metadata'] = {
                'execution_time_seconds': round(execution_time, 2),
                'timestamp': datetime.now().isoformat()
            }
        
        # Store error in agent outputs
        agent_outputs = state.get('agent_outputs', {}).copy()
        agent_outputs[tool_name] = error_result
        
        update_dict = {"agent_outputs": agent_outputs}
        
        # Track error counts and retries if requested
        if track_errors:
            retry_counts = state.get("retry_counts", {}).copy()
            retry_counts[tool_name] = retry_counts.get(tool_name, 0) + 1
            
            consecutive_failures = state.get('consecutive_failures', {}).copy()
            consecutive_failures[tool_name] = consecutive_failures.get(tool_name, 0) + 1
            
            update_dict.update({
                "total_error_count": state.get("total_error_count", 0) + 1,
                "retry_counts": retry_counts,
                "consecutive_failures": consecutive_failures,
                "last_node_executed": f"{tool_name}_tool"
            })
        
        return update_dict
