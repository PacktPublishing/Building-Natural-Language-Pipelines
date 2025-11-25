# Chapter 9: Advanced AI Agent Architectures

This chapter explores context engineering patterns for building efficient AI agents, demonstrating how strategic state management and architectural decisions impact token usage and cost.

In Chapter 8, we explored how agents work and compared frameworks.  Now we'll examine an advanced concern: **How do architectural choices  affect token efficiency and production readiness?**

## Prerequisites from Earlier Chapters

- [**Chapter 2**](../ch2/README.md): LangGraph state management, conditional routing
- [**Chapter 7**](../ch7-hayhooks/README.md): Refresh basics of deploying a pipeline as a REST endpoint via Hayhooks
- [**Chapter 8**](../ch8/yelp-navigator/README.md): Uses pipelines developed in Chapter 8 as REST endpoints for a LangGraph-based agent.
- [**Chapter 8**](../ch8/yelp-navigator/langgraph_multiagent_supervisor.ipynb): Agent graph patterns

If you need to review these concepts, refer back to the relevant chapters.

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
	# ============================================================================
	# API KEYS - Configure at least one LLM provider
	# ============================================================================

	# LLM Providers (choose one or more):

	# OpenAI (GPT models) - Default provider
	OPENAI_API_KEY=your_openai_key_here
	OPENAI_MODEL=gpt-4o-mini
	OPENAI_CHAT_MODEL=gpt-4o-mini

	# ============================================================================
	# OPTIONAL: LangSmith Tracing & Monitoring
	# ============================================================================

	LANGSMITH_API_KEY=your_langsmith_key_here
	LANGCHAIN_TRACING_V2=false 
	LANGCHAIN_PROJECT=yelp-navigator-LangGraph-Local

	# ============================================================================
	```
	
	To obtain the API keys:
	- **OpenAI**: Sign up at [OpenAI's platform](https://platform.openai.com)
	- **LangSmith** (optional): Sign up at [LangSmith](https://smith.langchain.com/)

	The agent explored in [context-engineering](./context-engineering/) supports GPT-OSS, DeepSeek-R1 and Qwen3. You can download Ollama and install the models to run the agent with local models instead of OpenAI. 

	[Install Ollama](https://ollama.com/download)

	```sh   
	# Pull the model - add the model you want to test
	ollama pull gpt-oss:20b
	```

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
| **Yelp Navigator V3** | Production-ready version using V2's supervisor pattern plus retry policies for transient failures and checkpointing for conversation persistence. Includes input guardrails for security. | Same as V2 | ✅ Retry policies, checkpointing, error tracking, input guardrails (prompt injection detection + PII sanitization) |

**Key Files:**
- `docs/ARCHITECTURE_COMPARISON.md` - Detailed comparison of all three architectures
- `docs/guardrails.md` - Complete guide to input guardrails (prompt injection + PII sanitization)
- `measure_token_usage.py` - Automated token measurement script with test scenarios
- `test_examples.sh` - Run all test cases to compare architectures
- `test_guardrails.py` - Test suite for input guardrails
- `shared/` - Common prompts and tools used by all versions
- `yelp-navigator-v3/persistence.md` - Guide to using checkpointing with in-memory and SQLite persistence

**What You'll Learn:**
- How state management design affects token consumption
- Trade-offs between monolithic and supervisor patterns
- Production-ready error handling with retry policies
- Conversation persistence with checkpointing
- Measuring and optimizing token usage in production agents
- Context reduction techniques (boolean flags vs full data)
- Implementing input guardrails for security (prompt injection detection + PII sanitization)

See the [context-engineering README](./context-engineering/README.md) for setup and usage instructions.

---

## Chapter Topics Covered

1. **Context Engineering** - Strategic management of information passed to LLMs
2. **State Management Patterns** - Monolithic vs dual-context architectures
3. **Supervisor Pattern** - Separating decision-making from tool execution
4. **Token Optimization** - Measuring and reducing token consumption
5. **Architectural Trade-offs** - When to use different patterns
6. **Production Features** - Retry policies, checkpointing, error handling, and input guardrails
7. **Security & Safety** - Prompt injection detection and PII sanitization
8. **Cost Analysis** - Token measurement and scaling implications