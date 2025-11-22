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

- **`yelp-navigator-v1/`** - Monolithic architecture (baseline for comparison)
- **`yelp-navigator-v2/`** - Supervisor pattern with efficient token usage
- **`yelp-navigator-v3/`** - Production-ready with retry policies + checkpointing
- **`shared/`** - Common tools, prompts, and configuration
- **`docs/`** - Architecture comparison and measurement guides

### Version Comparison

| Feature | V1 | V2 | V3 |
|---------|----|----|-----|
| Token Efficiency | Baseline | 16-50% better | 16-50% better |
| Architecture | Monolithic agents | Supervisor pattern | Supervisor pattern |
| Error Handling | Basic | Basic | Retry policies + graceful degradation |
| Persistence | None | None | Checkpointing (thread-based) |
| Error Tracking | None | None | Execution metadata + retry counts |
| Production Ready | ❌ Learning | ⚠️ Prototype | ✅ Production |

![](./docs/v1-v2-v3.png)

**Choose:**
- **V1** for learning monolithic agent patterns
- **V2** for understanding supervisor patterns and token optimization
- **V3** for production deployments requiring reliability and persistence

---

## Measure Token Efficiency

**Quick test:**
```sh
uv run python measure_token_usage.py
```

**Test complexity scaling:**
```sh
# Simple: ~16% savings (V2/V3 vs V1)
uv run python measure_token_usage.py --test-query "Italian restaurants" --test-location "Boston, MA" --detail-level general

# Complex: ~50% savings (V2/V3 vs V1, estimated)
uv run python measure_token_usage.py --test-query "sushi restaurants" --test-location "New York, NY" --detail-level reviews
```

**Run all tests:**
```sh
./test_examples.sh
```

**Note:** V2 and V3 have identical token efficiency since V3 uses the same supervisor pattern. V3 adds production features (retry policies, checkpointing) without impacting token usage.

See [`docs/ARCHITECTURE_COMPARISON.md`](./docs/ARCHITECTURE_COMPARISON.md) for detailed architecture analysis.
