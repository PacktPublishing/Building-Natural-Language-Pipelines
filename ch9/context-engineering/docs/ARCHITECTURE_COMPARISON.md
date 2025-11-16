# Yelp Navigator: V1 vs V2 Architecture Comparison

This document compares two architectural approaches for the Yelp Navigator agent, focusing on state management strategies and their impact on token efficiency.

## Architectural Overview

### V1: Sequential Node-Based Design
```
START → Clarification → Search → Details → Sentiment → Summary → Supervisor → END
                ↑                                                     ↓
                └─────────────── Approval Loop ──────────────────────┘
```

- **Sequential nodes**: Each node handles both tool execution and decision-making
- **Single state object**: All data in one TypedDict with 13+ fields
- **Hard-coded routing**: Conditional edges define workflow
- **State-driven**: Nodes decide next steps via `next_agent` field

### V2: Supervisor Pattern with Tool Separation
```
START → Clarify → ┌─ Supervisor ─┐ → Summary → END
                  │     ↓         │
                  │   Search      │
                  │     ↓         │
                  │   Details     │
                  │     ↓         │
                  │   Sentiment   │
                  └───────────────┘
```

- **Separated concerns**: Tools execute, agents reason
- **Modular state**: Structured fields with clear purpose
- **Dynamic routing**: Supervisor makes LLM-driven decisions
- **Command pattern**: Explicit flow control with LangGraph Commands

## State Management Comparison

### V1 State: Monolithic Dictionary
**Location:** `yelp-navigator-v1/app/state.py`

```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add]
    user_query: str
    clarified_query: str
    clarified_location: str
    next_agent: str                    # Routing logic
    agent_outputs: Dict[str, Any]      # Unstructured blob
    final_summary: str
    approval_attempts: int
    # ... 13 total fields
```

**Problems:**
- Unstructured `agent_outputs` stores all tool results generically
- Workflow state mixed with data (`next_agent`, flags)
- Deep nesting required to access pipeline outputs
- No clear separation of concerns

### V2 State: Structured and Purposeful
**Location:** `yelp-navigator-v2/app/state.py`

```python
class AgentState(MessagesState):
    search_query: str = ""
    search_location: str = ""
    detail_level: str = "general"
    
    # Dual context streams
    raw_results: Annotated[List[str], operator.add] = []  # For LLM
    pipeline_data: Dict[str, Any] = {}                     # For tools
    
    final_summary: str = ""
```

**Key Innovation - Dual Context Streams:**
1. **`raw_results`**: Human-readable summaries for LLM reasoning
2. **`pipeline_data`**: Structured data for tool chaining

**Benefits:**
- 7 focused fields vs 13 mixed-purpose fields
- Explicit data flow between tools
- Incremental context accumulation with `operator.add`
- No workflow coupling in state

## Token Efficiency Impact

**Measured Results** (see [Token Measurement Guide](TOKEN_MEASUREMENT_README.md))

| Scenario | V1 Tokens | V2 Tokens | Reduction |
|----------|-----------|-----------|-----------|
| **General Search** | 1,050 | 555 | 47% |
| **Detailed Search** | 3,072 | 707 | 77% |
| **Reviews Search** | 5,167 | 711 | 86% |
| **Average** | 3,107 | 652 | **79%** |

### Why This Matters

**Cost Savings (GPT-4 @ $0.03/1K tokens):**
- At 10,000 queries/month: **$730/month saved**
- Annual savings: **$8,760/year**

**Architectural Drivers of Token Reduction:**

1. **Progressive Context Building**: V2 accumulates context incrementally instead of rebuilding from scratch
2. **Supervisor Efficiency**: Minimal context for routing decisions (300-500 tokens vs 2,500+ tokens)
3. **Dual Context Streams**: Separate human-readable summaries from structured tool data
4. **Structured Outputs**: Pydantic models reduce parsing overhead

## Key Architectural Patterns

### The "Pipeline Data" Pattern

**V1 Approach:**
```python
# Deep nesting required
agent_outputs["search"]["full_output"]["result"]["businesses"]
```

**V2 Approach:**
```python
# First-class state field
state["pipeline_data"]
```

This enables:
- Clear data lineage between tools
- Easier debugging and testing
- Potential for caching by query hash

### Progressive Disclosure

**V1:** All agents see full context → token bloat  
**V2:** Each node receives minimal necessary context:
- Clarification: Just the query
- Supervisor: Only accumulated summaries
- Summary: Full context for final generation

## Conclusion

V2's state management demonstrates how **architectural decisions directly impact token efficiency**:

- **79% average token reduction** through structured state separation
- **Cleaner codebase** with explicit data flow
- **Better testability** via stateless, composable tools
- **Easier maintenance** with clear separation of concerns

**Note:** Both V1 and V2 use a node-based architecture (`nodes.py`). The key difference is not in the code organization, but in:
1. **State structure**: V1 uses monolithic state with `agent_outputs` blob; V2 uses dual context streams
2. **Routing control**: V1 uses state-driven routing (`next_agent` field); V2 uses supervisor-driven routing with Commands
3. **Context management**: V1 passes full state to each node; V2 uses progressive disclosure

**Measurement Methodology:** Token counts obtained using `tiktoken` with actual V1/V2 prompt templates and realistic pipeline data. Run your own measurements:

```bash
uv run python measure_token_usage.py --run-all-tests
```

See [TOKEN_MEASUREMENT_README.md](TOKEN_MEASUREMENT_README.md) for detailed instructions.
