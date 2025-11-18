# Yelp Navigator V3 - Memory-Aware Business Search Agent

## Overview

Yelp Navigator V3 is an enhanced version of the business search agent that incorporates **persistent memory** using SQLite. This enables the agent to:

1. **Remember businesses** from previous searches
2. **Answer follow-up questions** without re-querying APIs
3. **Reduce API calls** by caching business information
4. **Build knowledge** about businesses over multiple conversations

## What's New in V3

### Memory System
- **SQLite-based persistence**: Business data is stored locally in `business_memory.db`
- **Three-tier caching**: 
  - Basic business info (name, rating, location, etc.)
  - Detailed information (website content)
  - Sentiment analysis (review summaries)

### Intelligent Cache Usage
- Tools automatically check memory before making API calls
- Follow-up questions use cached data when available
- State tracks which businesses have cached information

### Enhanced State Management
- `known_business_ids`: List of business IDs from current session
- `cached_businesses`: Dictionary tracking what data is available for each business
- `current_business_focus`: Tracks which business is being discussed

## Architecture

### Key Components

1. **memory.py**: BusinessMemory class manages SQLite database
   - Store/retrieve business information
   - Track cached data availability
   - Simple, efficient queries

2. **tools.py**: Memory-aware tool wrappers
   - `search_businesses_with_memory()`: Searches and caches results
   - `get_business_details_with_memory()`: Checks cache before API calls
   - `analyze_reviews_sentiment_with_memory()`: Uses cached sentiment when available
   - `get_cached_business_info()`: Retrieves all cached data for a business

3. **nodes.py**: Enhanced node logic
   - `check_memory_node`: New node that checks if cached data can answer the query
   - Memory-aware routing in `clarify_intent_node`
   - Cache-first approach in all tool nodes

4. **state.py**: Extended AgentState
   - Memory tracking fields
   - Business focus tracking for follow-ups

## How It Works

### First Query Flow
```
User: "Find Italian restaurants in Boston"
  ↓
clarify_intent_node → supervisor_node → search_tool_node
  ↓
Search API called → Results cached in SQLite
  ↓
summary_node → Return results to user
```

### Follow-up Query Flow (Cache Hit)
```
User: "What do people say about the first one?"
  ↓
clarify_intent_node (recognizes follow-up)
  ↓
check_memory_node (finds reviews in cache)
  ↓
summary_node (uses cached data) → Return results
NO API CALLS MADE! ✨
```

### Follow-up Query Flow (Cache Miss)
```
User: "What do people say about the first one?"
  ↓
clarify_intent_node → check_memory_node
  ↓
Cache check: No review data found
  ↓
supervisor_node → sentiment_tool_node
  ↓
API called → Results cached → summary_node
```

## Database Schema

### businesses table
- `business_id` (PRIMARY KEY)
- `name`, `rating`, `review_count`
- `categories`, `price_range`, `phone`
- `location`, `website`
- `created_at`, `updated_at`

### business_details table
- `business_id` (FOREIGN KEY)
- `website_content`, `has_website_info`
- `content_length`, `fetched_at`

### business_sentiment table
- `business_id` (FOREIGN KEY)
- `total_reviews`, `positive_count`, `neutral_count`, `negative_count`
- `overall_sentiment`, `sentiment_data`
- `analyzed_at`

## Usage Example

```python
from yelp_navigator_v3.app.graph import graph

# First query - fetches from API and caches
result1 = graph.invoke({
    "messages": [{"role": "user", "content": "Find coffee shops in Seattle"}]
})

# Follow-up query - uses cached data
result2 = graph.invoke({
    "messages": [
        {"role": "user", "content": "Find coffee shops in Seattle"},
        {"role": "assistant", "content": result1["messages"][-1].content},
        {"role": "user", "content": "Show me reviews for the first one"}
    ]
})
# This will check cache first and may avoid API calls!
```

## Memory Management

### Checking Cached Businesses
```python
from yelp_navigator_v3.app.tools import list_cached_businesses

# Get all cached businesses
cached = list_cached_businesses()
print(f"I have {len(cached)} businesses in memory")
```

### Getting Cached Info
```python
from yelp_navigator_v3.app.tools import get_cached_business_info

# Get all available data for a business
info = get_cached_business_info("business_id_here")
if info:
    print(f"Business: {info['business']['name']}")
    print(f"Has details: {info['has_details']}")
    print(f"Has sentiment: {info['has_sentiment']}")
```

### Clearing Cache
```python
from yelp_navigator_v3.app.memory import BusinessMemory

memory = BusinessMemory()
memory.clear_all()  # Clear all cached data
```

## Benefits

1. **Faster Response Times**: Follow-up questions are answered instantly from cache
2. **Reduced API Costs**: Fewer calls to external APIs
3. **Better Conversations**: Agent remembers context from previous queries
4. **Persistent Knowledge**: Cache persists across sessions

## Configuration

The memory system can be configured in `configuration.py`:

```python
@dataclass(kw_only=True)
class Configuration:
    use_memory: bool = True  # Enable/disable memory
    memory_db_path: Optional[str] = None  # Custom DB path
```

## Testing the Memory Feature

To test the memory capabilities:

1. Start with a search query:
   ```
   "Find pizza places in New York"
   ```

2. Ask a follow-up about reviews:
   ```
   "What do people say about the first one?"
   ```

3. The agent will:
   - Recognize you're asking about a cached business
   - Check memory for sentiment data
   - Either return cached data (fast!) or fetch and cache it

## Comparison with V2

| Feature | V2 | V3 |
|---------|----|----|
| Follow-up Questions | Re-queries API | Uses cache when possible |
| Memory | None | SQLite persistence |
| API Calls | Every request | Cached when available |
| State Tracking | Basic | Enhanced with memory fields |
| Performance | Consistent | Faster for follow-ups |

## Limitations

- Cache does not expire automatically (could add TTL in future)
- Database grows over time (could add cleanup in future)
- Memory is local to the machine (could use Redis for distributed systems)

## Future Enhancements

- [ ] Add cache expiration (TTL)
- [ ] Add cache size limits
- [ ] Support for Redis or other distributed caches
- [ ] Cache statistics and monitoring
- [ ] Automatic cache warming
- [ ] Smart cache invalidation

## Dependencies

- `sqlite3` (built-in Python library)
- All dependencies from V2 (LangChain, LangGraph, etc.)

No additional dependencies required! 🎉
