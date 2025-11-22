# V3 Persistence Examples

These scripts demonstrate how to use checkpointing in V3 for conversation persistence.

## Running the Examples

**Important:** Run these scripts from the `yelp-navigator-v3` directory:

```sh
cd yelp-navigator-v3/
```

### 1. In-Memory Persistence (`inmemory_persistence.py`)

Uses `MemorySaver` for basic in-memory persistence (conversation memory lasts only during script execution):

```sh
uv run python inmemory_persistence.py
```

**What it demonstrates:**
- Initial search: "Find coffee shops in Seattle"
- Follow-up: "Which one has the best reviews?" (agent remembers Seattle and coffee shops)
- Memory persists only while the script runs

**Use case:** Quick testing, development, single-session interactions

### 2. SQLite Persistence (`sqlite_persistence.py`)

Uses `SqliteSaver` for durable persistence (conversation memory survives restarts):

```sh
uv run python sqlite_persistence.py
```

**What it demonstrates:**
- Creates `memory.sqlite` database file
- Search: "Find pizza in Chicago"
- Memory persists across script runs (restart with same `thread_id` to continue)

**Use case:** Production deployments, multi-session conversations, user history

## Key Concepts

### Thread IDs
```python
config = {"configurable": {"thread_id": "user_session_123"}}
```

The `thread_id` is the key to accessing conversation history:
- Same `thread_id` = continues conversation
- Different `thread_id` = starts fresh conversation

### Checkpointer Options

| Checkpointer | Persistence | Use Case |
|---|---|---|
| `MemorySaver()` | In-memory (temporary) | Development, testing |
| `SqliteSaver(conn)` | SQLite database (durable) | Production, user sessions |

### Graph Configuration

The V3 graph builder supports flexible checkpointing:

```python
from app.graph import get_graph_with_persistence

# Default: MemorySaver
graph = get_graph_with_persistence()

# Custom: SQLite
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
conn = sqlite3.connect("memory.sqlite", check_same_thread=False)
graph = get_graph_with_persistence(checkpointer=SqliteSaver(conn))

# No persistence
graph = get_graph_with_persistence(checkpointer=False)
```

## Production Considerations

1. **Thread Management**: Use unique user IDs or session IDs as `thread_id`
2. **Database Maintenance**: Periodically clean old conversations from SQLite
3. **Concurrency**: SQLite with `check_same_thread=False` for multi-threaded apps
4. **Scalability**: Consider PostgreSQL checkpointer for high-volume production

## Troubleshooting

**ModuleNotFoundError: No module named 'shared'**
- Make sure to run scripts from the `yelp-navigator-v3` directory
- The scripts add parent directory to Python path automatically

**Import Error: langgraph.checkpoint.sqlite**
- Install: `uv add langgraph-checkpoint-sqlite` (from `ch9/` directory)
