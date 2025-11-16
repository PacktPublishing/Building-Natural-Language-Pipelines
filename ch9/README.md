# Chapter 9: Advanced AI Agent Architectures

This repository contains advanced exercises exploring Model Context Protocol (MCP), Agent-to-Agent (A2A) communication, and context engineering patterns for building efficient AI agents.

## Setup Instructions

1. **Install [uv](https://docs.astral.sh/uv/getting-started/installation/):**
	```sh
	pip install uv
	```
2. **Install dependencies:**
	```sh
	uv sync
	```
3. **Activate the virtual environment:**
	```sh
	source .venv/bin/activate
	```
4. **(Recommended) Open this `ch9` folder in a new VS Code window.**
5. **Select the virtual environment as the Jupyter kernel:**
	- Open any notebook.
	- Click the kernel picker (top right) and select the `.venv` environment.

6. **Set up API keys:**

Create a `.env` file in the relevant subdirectory with your API keys:
```sh
OPENAI_API_KEY=your_openai_key_here
YELP_API_KEY=your_yelp_key_here
TAVILY_API_KEY=your_tavily_key_here
```

To obtain the API keys:
- OpenAI API key: Sign up at [OpenAI's platform](https://platform.openai.com)
- Yelp Business Review API key: Register at [Yelp Business Review RapidAPI](https://rapidapi.com/beat-analytics-beat-analytics-default/api/yelp-business-reviewss)
- Tavily API key: Register at [Tavily](https://tavily.com)

7. **LangGraph Studio (Optional):**

For visual debugging and testing of LangGraph agents, get a LangSmith API key [LangSmith Observability](https://www.langchain.com/langsmith/observability).

---

## Contents

### Context Engineering

The `context-engineering/` folder contains advanced examples demonstrating token-efficient agent architectures:

| Example | Description |
|---|---|
| **Yelp Navigator V1** | Monolithic agent-centric design with tightly coupled agents and single state management |
| **Yelp Navigator V2** | Supervisor pattern with tool separation for improved token efficiency and modularity |
| **Architecture Comparison** | Detailed analysis of design patterns, token usage, and architectural trade-offs |
| **Token Measurement** | Tools and reports for measuring and comparing token usage across agent architectures |

Key files:
- `ARCHITECTURE_COMPARISON.md` - Comprehensive comparison of V1 vs V2 architectural approaches
- `TOKEN_MEASUREMENT_README.md` - Guide to measuring and analyzing token consumption
- `measure_token_usage.py` - Script for automated token usage measurement
- `token_usage_report.md` - Detailed token usage analysis and recommendations

### Model Context Protocol (MCP)

The `mcp/` folder contains examples of integrating Model Context Protocol for enhanced agent capabilities.

### Agent-to-Agent (A2A)

The `a2a/` folder contains examples of multi-agent systems communicating and collaborating.

---

## Chapter Topics Covered

1. Advanced agent architecture patterns
2. Context engineering for token efficiency
3. Supervisor pattern vs monolithic agent design
4. Model Context Protocol (MCP) integration
5. Agent-to-Agent (A2A) communication
6. State management strategies
7. Token usage optimization
8. Tool separation and modularity