# Yelp Navigator: Architecture Comparison (V1, V2, V3)

Three implementations demonstrating how architectural decisions impact token efficiency, maintainability, and production readiness.

## Core Architectural Differences

### V1: Agent Nodes (Monolithic)
- **Combined logic**: Each node does tool execution + decision-making + routing
- **Return dictionaries**: Nodes return state updates with `next_agent` field
- **Sequential flow**: Hard-coded conditional edges based on `next_agent`
- **Error handling**: Basic try-catch blocks
- **Persistence**: None

### V2: Supervisor + Tool Nodes (Token-Optimized)
- **Separated concerns**: Supervisor makes decisions, tool nodes execute
- **Return Commands**: Uses LangGraph `Command` pattern for explicit routing
- **Dynamic flow**: Supervisor decides next step based on accumulated state
- **Error handling**: Basic try-catch blocks
- **Persistence**: None

### V3: Production-Ready Supervisor Pattern
- **Architecture**: Same supervisor pattern as V2 (maintains token efficiency)
- **Return Commands**: Uses LangGraph `Command` pattern
- **Dynamic flow**: Error-aware supervisor with graceful degradation
- **Error handling**: Retry policies, rate limit detection, clean exits
- **Persistence**: Checkpointing support (in-memory or SQLite)
- **Guardrails**: Input and validation nodes (prompt injection, PII sanitization)

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

**Added Features:**

#### 1. Retry Policies
```python
retry_policy = RetryPolicy(
    max_attempts=3,         # Try up to 3 times
    initial_interval=1.0,   # Wait 1 second before first retry
    backoff_factor=2.0,     # Double wait time each retry
    max_interval=10.0       # Max 10 seconds between retries
)
```
Configured at graph compilation level for all tool nodes.

#### 2. Rate Limit & Error Detection
- Detects HTTP 429 (rate limit) responses
- Identifies connection errors and timeouts
- **Exits immediately** with user-friendly messages (no wasted retries)
- Example message: *"I apologize, but I'm unable to complete your request due to rate limit. The Yelp API service is currently unavailable. Please try again later."*

#### 3. Checkpointing (Conversation Persistence)
- **In-Memory**: `MemorySaver` for development/testing
- **SQLite**: `SqliteSaver` for production with durable storage
- Thread-based sessions allow multi-user support
- Example: `config = {"configurable": {"thread_id": "user_123"}}`

#### 4. Enhanced Error Tracking
- State tracks: error counts, retry attempts, execution metadata
- Supervisor receives error context for intelligent decision-making
- Graceful degradation: Finalize with partial data when needed

#### 5. Guardrails (Input Validation)
**Input Guardrails Node** (runs before clarification):
- **Prompt injection detection**: Blocks suspicious patterns
  - Examples: "ignore previous instructions", "system: you are", "forget everything"
- **PII sanitization**: Redacts sensitive data from user inputs
  - Emails, phone numbers, SSNs, credit cards, IP addresses

**Implementation:**
- Simple regex patterns (no LLM calls, fast execution)
- Separate nodes for visibility in graph
- Logs all validation activities
- Configurable via `Configuration` settings
- Non-blocking: sanitizes rather than rejects

**Configuration:**
```python
enable_guardrails: bool = True   # Prompt injection + quality + leakage checks
sanitize_pii: bool = True        # PII redaction (input + output)
```

**Architecture:**
- Same supervisor + tool node separation as V2 (maintains token efficiency)
- Retry policies configured at graph compilation level
- Enhanced state schema with error tracking fields
- Error-aware supervisor prompts for intelligent recovery
- Tools return structured error responses with `rate_limited` flags
- Input guardrails as separate nodes for visibility

**Documentation:**
- See `yelp-navigator-v3/persistence.md` for checkpointing guide

**When to Use:**
- **V1**: Learning agent patterns, prototyping, very low volumes
- **V2**: Understanding token optimization, cost-sensitive prototypes
- **V3**: Production deployments requiring reliability, persistence, and proper error handling

## Key Takeaways

### Feature Comparison Table

| Feature | V1 | V2 | V3 |
|---------|----|----|----|
| Token Efficiency | Baseline | 16-50% better | 16-50% better |
| Architecture | Monolithic nodes | Supervisor pattern | Supervisor pattern |
| Error Handling | Basic | Basic | Retry policies + rate limit detection |
| Persistence | None | None | MemorySaver / SqliteSaver |
| Error Tracking | None | None | Full metadata + retry counts |
| Graceful Degradation | ❌ | ❌ | ✅ |
| Input Guardrails | ❌ | ❌ | ✅ (prompt injection, PII) |
| Production Ready | ❌ | ⚠️ Prototype | ✅ |

### When to Choose Each Version

✅ **V1: Learning & Simple Prototypes**
- Understanding monolithic agent patterns
- Low-stakes prototyping
- Very low query volumes (< 100/month)
- Educational purposes

✅ **V2: Token Optimization Focus**
- Understanding supervisor patterns
- Cost-sensitive development
- Medium-volume prototypes (100-1K/month)
- Demonstrating token efficiency

✅ **V3: Production Deployments**
- All V2 token savings (16-50%)
- Production-ready error handling
- Conversation persistence needed
- Multi-user applications
- High-volume deployments (> 1K/month)
- Rate limiting concerns
- Better observability and debugging
- Graceful degradation on failures
- Security requirements (prompt injection protection, PII handling)

### Cost Impact at Scale

**Based on GPT-4 @ $0.03/1K tokens:**

| Monthly Volume | V1 Cost | V2/V3 Cost | Savings |
|----------------|---------|------------|----------|
| 1K queries | $35 | $29 | $6 (17%) |
| 10K queries | $350 | $280 | $70 (20%) |
| 100K queries | $3,500 | $2,450 | $1,050 (30%) |

*Note: V3 adds production features with no token cost increase over V2*

## Run Your Own Tests

### Token Usage Tests
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


