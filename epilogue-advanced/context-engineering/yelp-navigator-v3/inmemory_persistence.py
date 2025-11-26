import sys
from pathlib import Path

# Add parent directory to path to allow imports from shared/
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.graph import get_graph_with_persistence
from langchain_core.messages import HumanMessage

# 1. Initialize the graph with the default MemorySaver (defined in your graph.py)
graph = get_graph_with_persistence() 

# 2. Define a thread configuration
# This ID is the "key" to the memory. Change it to start a fresh conversation.
config = {"configurable": {"thread_id": "user_session_123"}}

print("--- Interaction 1: Initial Search ---")
print("User: Find coffee shops in Seattle\n")
input_1 = {
    "messages": [HumanMessage(content="Find coffee shops in Seattle")]
}

# Run the graph
for update in graph.stream(input_1, config=config):
    for node_id, value in update.items():
        # Check if this update contains messages and print the last AI message
        if value and isinstance(value, dict) and "messages" in value and value["messages"]:
            last_message = value["messages"][-1]
            if hasattr(last_message, 'content') and last_message.content:
                print(f"\n[{node_id}] Agent: {last_message.content}\n")

print("\n" + "="*80)
print("--- Interaction 2: Follow-up (Testing Persistence) ---")
print("User: Which one has the best reviews?\n")
# We do NOT state the location again. The agent must remember "Seattle" and "Coffee shops"
# from the checkpoint associated with "user_session_123".
input_2 = {
    "messages": [HumanMessage(content="Which one has the best reviews?")]
}

for update in graph.stream(input_2, config=config):
    for node_id, value in update.items():
        # Check if this update contains messages and print the last AI message
        if value and isinstance(value, dict) and "messages" in value and value["messages"]:
            last_message = value["messages"][-1]
            if hasattr(last_message, 'content') and last_message.content:
                print(f"\n[{node_id}] Agent: {last_message.content}\n")