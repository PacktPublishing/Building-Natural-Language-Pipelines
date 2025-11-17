# Yelp Navigator: V1 vs V2 Architecture Comparison

Two approaches to building a context-efficient AI agent, demonstrating how state management impacts token usage and maintainability.

## Core Architectural Difference

### V1: Monolithic State
Every node receives the full state object with all accumulated data.

### V2: Dual Context Streams  
Separates human-readable summaries (for LLM) from structured data (for tools).

## State Management

### V1: Monolithic State (13 fields)

```python
class AgentState(TypedDict):
    agent_outputs: Dict[str, Any]  # All tool results nested here
    next_agent: str                # Routing logic in state
    # ... 11 more fields
```

**Issue:** Every node receives the entire `agent_outputs` blob with all accumulated data.

### V2: Dual Context Streams (7 fields)

```python
class AgentState(MessagesState):
    raw_results: List[str]       # Summaries for LLM
    pipeline_data: Dict[str, Any] # Structured data for tools
    # ... 5 more fields
```

**Benefit:** LLM sees only concise summaries; tools access structured data separately.

## Token Efficiency

**Measured Results:**

| Scenario | V1 Tokens | V2 Tokens | Reduction |
|----------|-----------|-----------|-----------|
| Simple query (general) | 1,167 | 981 | **16%** |
| Complex query (detailed/reviews) | ~2,500 | ~1,200 | **~50%** (estimated) |

### Why V2 Saves Tokens

1. **Supervisor sees minimal context**: Boolean flags instead of full state
2. **Summary uses concise data**: `raw_results` summaries vs. nested `agent_outputs`  
3. **Progressive disclosure**: Each node gets only what it needs

### Cost Impact (GPT-4 @ $0.03/1K tokens)

- **10K simple queries/month**: ~$56/month savings
- **10K mixed queries/month**: ~$300/month savings (estimated)

## Example: How Token Usage Differs

### V1 Summary Prompt (1,200+ tokens)
```python
# Summary node receives entire agent_outputs
summary_prompt = f"""
Create summary from:
{json.dumps(state['agent_outputs'])}  # Full nested data
"""
```

### V2 Summary Prompt (100 tokens)
```python
# Summary node receives concise summaries
summary_prompt = f"""
Create summary from:
{state['raw_results']}  # ["Search: Found 10 businesses", "Sentiment: 80% positive"]
"""
```

## Key Takeaways

✅ **V2 advantages:**
- 16-50% token savings (scales with query complexity)
- Cleaner separation of concerns
- Easier to debug and test
- Better for production workloads

⚠️ **V1 is simpler for:**
- Learning/prototyping
- Very low query volumes

## Run Your Own Tests

```bash
# Simple query test
uv run python measure_token_usage.py \
    --test-query "Italian restaurants" \
    --test-location "Boston, MA" \
    --detail-level general

# Complex query test  
uv run python measure_token_usage.py \
    --test-query "sushi restaurants" \
    --test-location "New York, NY" \
    --detail-level reviews
```

See [TOKEN_MEASUREMENT_README.md](TOKEN_MEASUREMENT_README.md) for details.
