# Context Engineering - Yelp Navigator

This folder contains two versions of the Yelp Navigator agent demonstrating different architectural approaches for context-efficient AI agents.

## Prerequisites

This project uses serialized Haystack pipelines from the `ch8/yelp-navigator` directory. You'll need to build and run those pipelines first.

### Step 1: Build and Run Haystack Pipelines

Complete the [setup instructions](../README.md#setup-instructions)

Navigate to the `ch8` directory and build the pipelines:

```sh
cd ../ch8/yelp-navigator
uv run ./build_all_pipelines.sh
```

Start the Hayhooks server to serve the pipelines:

```sh
uv run hayhooks run --pipelines-dir pipelines
```

**Note** Please ensure you have an active Yelp Business Review API key. For more information about how these endpoints work, please review the [Yelp Navigator Hayhooks Guide](../../ch8/yelp-navigator/yelp-navigator-hayhooks-guide.md).

Leave this terminal running.

### Step 2: Set Up API Keys

Create a `.env` file in the `ch9/context-engineering` directory with your API keys (use `.env.example` as a template):

```sh
OPENAI_API_KEY=your_openai_api_key

# Optional for LangSmith tracing
LANGSMITH_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=context-engineering-LangGraph-Local
```

To obtain the API keys:
- OpenAI API key: Sign up at [OpenAI's platform](https://platform.openai.com)
- LangSmith API key: Sign up at [LangSmith](https://smith.langchain.com/) (optional, for tracing and debugging)

### Step 3: Run LangGraph Studio

In a separate terminal from the `ch9/context-engineering` directory, start the LangGraph development server:

```sh
cd ch9/context-engineering/
uv run langgraph dev
```

This will automatically open LangGraph Studio in your browser, where you can visually interact with and debug the agents.
If it doesn't pop up automatically, open

```bash
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```
---

## Contents

### Yelp Navigator V1
- **Location**: `yelp-navigator-v1/`
- **Architecture**: Monolithic agent-centric design with tightly coupled agents
- **State Management**: Single state object with all fields

### Yelp Navigator V2
- **Location**: `yelp-navigator-v2/`
- **Architecture**: Supervisor pattern with tool separation
- **State Management**: Minimal state with focused agent responsibilities

### Documentation
- [`ARCHITECTURE_COMPARISON.md`](./docs/ARCHITECTURE_COMPARISON.md) - Detailed comparison of V1 vs V2 architectures
- [`TOKEN_MEASUREMENT_README.md`](./docs/TOKEN_MEASUREMENT_README.md) - Guide to measuring token usage
- `measure_token_usage.py` - Token measurement automation script
- `token_usage_report.md` - Token usage analysis and recommendations

---

## Using LangGraph Studio

Once LangGraph Studio opens:

1. Select the agent version you want to test (V1 or V2)
2. Enter your query in the input field
3. Watch the agent workflow execute with visual feedback
4. Inspect state changes, tool calls, and token usage at each step
5. Use the debugging tools to understand agent decision-making

---

## Token Usage Comparison

Run the token measurement script to compare efficiency:

```sh
uv run python measure_token_usage.py
```

See `token_usage_report.md` for detailed analysis of architectural trade-offs.