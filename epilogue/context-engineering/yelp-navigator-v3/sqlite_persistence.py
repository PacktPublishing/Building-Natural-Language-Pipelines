import sys
from pathlib import Path
import sqlite3

# Add parent directory to path to allow imports from shared/
sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph.checkpoint.sqlite import SqliteSaver
from app.graph import get_graph_with_persistence
from langchain_core.messages import HumanMessage

# 1. Setup a SQLite connection
conn = sqlite3.connect("memory.sqlite", check_same_thread=False)
checkpointer = SqliteSaver(conn)

# 2. Pass the specific checkpointer to your graph builder
graph = get_graph_with_persistence(checkpointer=checkpointer)

# 3. Use the same config pattern
config = {"configurable": {"thread_id": "persistent_session_01"}}

# Interaction 1
print("--- Interaction 1 ---")
print("User: Find pizza in Chicago\n")

for update in graph.stream(
    {"messages": [HumanMessage(content="Find pizza in Chicago")]}, 
    config=config
):
    for node_id, value in update.items():
        # Check if this update contains messages and print the last AI message
        if value and isinstance(value, dict) and "messages" in value and value["messages"]:
            last_message = value["messages"][-1]
            if hasattr(last_message, 'content') and last_message.content:
                print(f"\n[{node_id}] Agent: {last_message.content}\n")

print("\n" + "="*80)
print("\nConversation saved to memory.sqlite with thread_id='persistent_session_01'")
print("Run this script again to continue the conversation, or modify the script")
print("to add more interactions below.\n")

# If you stop this script here and run it again later with the same 
# thread_id, it will remember the pizza search.