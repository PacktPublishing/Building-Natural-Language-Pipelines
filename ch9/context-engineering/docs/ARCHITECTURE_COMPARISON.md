# Yelp Navigator: V1 vs V2 Architecture Comparison

Two approaches to building a context-efficient AI agent, demonstrating how state management impacts token usage and maintainability.

## Core Architectural Differences

### V1: Agent Nodes
- **Combined logic**: Each node does tool execution + decision-making + routing
- **Return dictionaries**: Nodes return state updates with `next_agent` field
- **Sequential flow**: Hard-coded conditional edges based on `next_agent`

### V2: Supervisor + Tool Nodes  
- **Separated concerns**: Supervisor makes decisions, tool nodes execute
- **Return Commands**: Uses LangGraph `Command` pattern for explicit routing
- **Dynamic flow**: Supervisor decides next step based on accumulated state

## Node Design Comparison

### V1: Agent Nodes (Combined Logic)

```python
def search_node(state: AgentState) -> AgentState:
    """Does everything: tool call + routing decision"""
    # 1. Execute tool
    result = search_businesses.invoke({"query": full_query})
    
    # 2. Store in agent_outputs
    agent_outputs["search"] = result
    
    # 3. Decide next step
    if detail_level == "general":
        next_agent = "summary"
    elif detail_level == "detailed":
        next_agent = "details"
    
    # 4. Return state update with routing
    return {"agent_outputs": agent_outputs, "next_agent": next_agent}
```

**Pattern**: Each node contains tool execution, state storage, and routing logic.

### V2: Supervisor + Tool Nodes (Separated)

```python
def supervisor_node(state: AgentState) -> Command:
    """Only decides what to do next"""
    decision = supervisor_model.invoke([SystemMessage(context)])
    return Command(goto=mapping[decision.next_action])

def search_tool_node(state: AgentState) -> Command:
    """Only executes the search tool"""
    result = search_businesses.invoke({"query": query})
    existing_outputs['search'] = result
    return Command(goto="supervisor", update={"agent_outputs": existing_outputs})
```

**Pattern**: Supervisor decides, tools execute, supervisor decides again.

## State Management

### V1: Monolithic (13 fields)

```python
class AgentState(TypedDict):
    agent_outputs: Dict[str, Any]  # All tool results nested here
    next_agent: str                # Routing logic in state
    # ... 11 more fields
```

**Issue:** Every node receives entire `agent_outputs` blob with all accumulated data.

### V2: Dual Context (7 fields)

```python
class AgentState(MessagesState):
    raw_results: List[str]       # Summaries for LLM (unused currently)
    agent_outputs: Dict[str, Any] # Tool results (same as V1)
    # ... 5 more fields
```

**Note:** V2 still uses `agent_outputs` for compatibility with shared summary prompt.

## Token Efficiency

**Measured Results:**

| Scenario | V1 Tokens | V2 Tokens | Reduction |
|----------|-----------|-----------|-----------|
| Simple query (general) | 1,167 | 981 | **16%** |
| Complex query (detailed/reviews) | ~2,500 | ~1,200 | **~50%** (estimated) |

### Why V2 Saves Tokens

1. **Supervisor uses boolean flags**: Sees `has_search_data=True` instead of full search results
2. **Multiple small LLM calls**: Supervisor routes with minimal context (300 tokens) multiple times
3. **V1 nodes see full state**: Each node receives entire accumulated `agent_outputs` blob

### Cost Impact (GPT-4 @ $0.03/1K tokens)

- **10K simple queries/month**: ~$56/month savings
- **10K mixed queries/month**: ~$300/month savings (estimated)

## Example: Token Savings Breakdown

### V1 Workflow (1,167 tokens for simple query)
```
Clarification (291) → Search (25) → Summary (482) → Supervisor Approval (379)
```
Each node sees full state; summary receives entire `agent_outputs`.

### V2 Workflow (981 tokens for simple query)  
```
Clarification (310) → Supervisor (311) → Search → Supervisor (311) → Summary (56)
```
Supervisor makes multiple routing decisions with boolean flags only (300 tokens each).

## V3: Production-Ready Enhancement

### V3 = V2 Architecture + Production Features

**Added Features (High Priority):**
1. **Retry Policies**: Automatic retries for transient failures (network, timeouts, rate limits)
2. **Checkpointing**: Conversation persistence via thread-based sessions
3. **Error Tracking**: State tracks errors, retry counts, execution metadata
4. **Graceful Degradation**: Supervisor can finalize with partial data on repeated failures

**Architecture:**
- Same supervisor + tool node separation as V2 (maintains token efficiency)
- Retry policies configured at graph compilation level
- Enhanced state schema with error tracking fields
- Error-aware supervisor prompts for intelligent recovery

**When to Use:**
- **V1**: Learning, prototyping, very low volumes
- **V2**: Production prototypes, cost-sensitive deployments
- **V3**: Production deployments requiring reliability and persistence

## Key Takeaways

✅ **V3 advantages:**
- All V2 token savings (16-50%)
- Production-ready error handling
- Conversation persistence
- Better observability and debugging
- Graceful degradation on failures

✅ **V2 advantages:**
- 16-50% token savings over V1
- Cleaner separation of concerns
- Good for production prototypes

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

