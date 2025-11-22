# Chapter 9: Advanced AI Agent Architectures

This chapter explores context engineering patterns for building efficient AI agents, demonstrating how strategic state management and architectural decisions impact token usage and cost.

## Setup Instructions

1. **Install [uv](https://docs.astral.sh/uv/getting-started/installation/):**
	```sh
	pip install uv
	```

2. **Set up API keys:**

	Copy the example environment file and populate it with your API keys:
	```sh
	cp .env.example .env
	```
	
	Then edit `.env` and add your API keys:
	```sh
	# Required
	OPENAI_API_KEY=your_openai_key_here
	YELP_API_KEY=your_yelp_key_here
	
	# Optional (for LangGraph Studio)
	LANGSMITH_API_KEY=your_langsmith_key_here
	LANGCHAIN_TRACING_V2=true
	LANGCHAIN_PROJECT=chapter-9-agents
	```
	
	To obtain the API keys:
	- **OpenAI**: Sign up at [OpenAI's platform](https://platform.openai.com)
	- **Yelp**: Register at [Yelp Business Review RapidAPI](https://rapidapi.com/beat-analytics-beat-analytics-default/api/yelp-business-reviews)
	- **LangSmith** (optional): Sign up at [LangSmith](https://smith.langchain.com/)

3. **Install dependencies:**
	```sh
	uv sync
	```

4. **Activate the virtual environment:**
	```sh
	source .venv/bin/activate
	```

5. **(Recommended) Open this `ch9` folder in a new VS Code window.**

6. **Select the virtual environment as the Jupyter kernel:**
	- Open any notebook.
	- Click the kernel picker (top right) and select the `.venv` environment.

---

## Contents

### Context Engineering (`context-engineering/`)

This folder demonstrates context engineering through three implementations of the same Yelp Navigator agent, showing how architectural decisions impact token efficiency and production readiness:

| Architecture | Description | Token Efficiency | Production Features |
|---|---|---|---|
| **Yelp Navigator V1** | Monolithic design where each agent node handles tool execution, decision-making, and routing. All tool results accumulate in a single `agent_outputs` dictionary that every node receives. | Baseline | None |
| **Yelp Navigator V2** | Supervisor pattern that separates concerns: a supervisor node makes routing decisions with minimal context (boolean flags), while dedicated tool nodes execute operations. | 16-50% fewer tokens | None |
| **Yelp Navigator V3** | Production-ready version using V2's supervisor pattern plus retry policies for transient failures and checkpointing for conversation persistence. | Same as V2 | ✅ Retry policies, checkpointing, error tracking |

**Key Files:**
- `docs/ARCHITECTURE_COMPARISON.md` - Detailed comparison of all three architectures
- `measure_token_usage.py` - Automated token measurement script with test scenarios
- `test_examples.sh` - Run all test cases to compare architectures
- `shared/` - Common prompts and tools used by all versions

**What You'll Learn:**
- How state management design affects token consumption
- Trade-offs between monolithic and supervisor patterns
- Production-ready error handling with retry policies
- Conversation persistence with checkpointing
- Measuring and optimizing token usage in production agents
- Context reduction techniques (boolean flags vs full data)

See the [context-engineering README](./context-engineering/README.md) for setup and usage instructions.

---

## Chapter Topics Covered

1. **Context Engineering** - Strategic management of information passed to LLMs
2. **State Management Patterns** - Monolithic vs dual-context architectures
3. **Supervisor Pattern** - Separating decision-making from tool execution
4. **Token Optimization** - Measuring and reducing token consumption
5. **Architectural Trade-offs** - When to use different patterns
6. **Production Features** - Retry policies, checkpointing, and error handling
7. **Cost Analysis** - Token measurement and scaling implications