# Context Engineering - Yelp Navigator

Three versions of the Yelp Navigator agent demonstrating how state management affects token efficiency and production readiness.

## Setup

1. **Complete main setup**: Follow [ch9 README setup](../README.md#setup-instructions) and configure `.env`

2. **Start Haystack pipelines**:
   ```sh
   cd ../../ch8/yelp-navigator
   uv run sh build_all_pipelines.sh
   sh start_hayhooks.sh  # Leave running
   ```

3. **Start LangGraph Studio**:
   ```sh
   cd ch9/context-engineering/
   uv run langgraph dev
   ```
   Opens at `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

---

## What's Inside

- **`yelp-navigator-v1/`** - Monolithic state (all data in `agent_outputs`)
- **`yelp-navigator-v2/`** - Supervisor pattern with efficient token usage
- **`yelp-navigator-v3/`** - **Production-ready** with retry policies + checkpointing
- **`shared/`** - Common tools, prompts, and configuration
- **`docs/`** - Architecture comparison and measurement guides

### Version Comparison

| Feature | V1 | V2 | V3 |
|---------|----|----|-----|
| Token Efficiency | Baseline | 16-50% better | Same as V2 |
| Architecture | Monolithic agents | Supervisor pattern | Supervisor pattern |
| Error Handling | Basic | Basic | **Retry policies** |
| Persistence | None | None | **Checkpointing** |
| Production Ready | ❌ | ⚠️ Prototype | ✅ **Yes** |

**Choose:**
- **V1** for learning and prototyping
- **V2** for cost-efficient production prototypes
- **V3** for production deployments requiring reliability

---

## Measure Token Efficiency

**Quick test:**
```sh
uv run python measure_token_usage.py
```

**Test complexity scaling:**
```sh
# Simple: ~16% savings
uv run python measure_token_usage.py --test-query "Italian restaurants" --test-location "Boston, MA" --detail-level general

# Complex: ~50% savings (estimated)
uv run python measure_token_usage.py --test-query "sushi restaurants" --test-location "New York, NY" --detail-level reviews
```

**Run all tests:**
```sh
./test_examples.sh
```

See [`docs/ARCHITECTURE_COMPARISON.md`](./docs/ARCHITECTURE_COMPARISON.md) for details on why V2 is more efficient.
