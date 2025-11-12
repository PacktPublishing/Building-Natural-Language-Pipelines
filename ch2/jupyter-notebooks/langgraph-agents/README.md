# Chapter 

This repository contains exercises and interactive notebooks for Chapter 2, introducing LangGraph's state-based agent framework and building intelligent agents with tools.

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
4. **(Recommended) Open this `ch2` folder in a new VS Code window.**
5. **Select the virtual environment as the Jupyter kernel:**
	- Open any notebook.
	- Click the kernel picker (top right) and select the `.venv` environment.

6. **Set up API keys:**

Create a `.env` file in the `jupyter-notebooks/langgraph-agents/` directory with your API keys:
```sh
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here
# OR
SERPER_API_KEY=your_serper_key_here
```

To obtain the API keys:
- OpenAI API key: Sign up at [OpenAI's platform](https://platform.openai.com)
- Tavily API key: Register at [Tavily](https://tavily.com) (recommended for AI applications)
- Serper API key: Register at [Serper.dev](https://serper.dev) (Google Search wrapper)

7. **(Optional) Install Ollama for local LLM inference:**

```sh
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from: https://ollama.com
```

Pull the Qwen2 model for local inference:
```sh
ollama pull qwen2:0.5b
```

---

## Contents

| Notebook | Link | Description |
|---|---|---|
| Create Simple Agent | [01_create-simple-agent.ipynb](./jupyter-notebooks/langgraph-agents/01_create-simple-agent.ipynb) | Build your first LangGraph agent with basic state management |
| Middleware Tutorial | [02_middleware-tutorial.ipynb](./jupyter-notebooks/langgraph-agents/02_middleware-tutorial.ipynb) | Learn to add middleware layers for logging, authentication, and monitoring |
| Multi-Agent Workflow | [03_multi-agent-workflow.ipynb](./jupyter-notebooks/langgraph-agents/03_multi-agent-workflow.ipynb) | Coordinate multiple specialized agents in a workflow |
| Understanding State Graph | [04_understanding-state-graph.ipynb](./jupyter-notebooks/langgraph-agents/04_understanding-state-graph.ipynb) | Deep dive into LangGraph's state management with MessagesState and reducers |
| Graph-Based Agent with Tools | [05_graph-based-agent-with-tools.ipynb](./jupyter-notebooks/langgraph-agents/05_graph-based-agent-with-tools.ipynb) | Build complete agents with external tool integration and conditional routing |
| Multi-Agent Systems Middleware | [06_multi-agent-systems-middleware.ipynb](./jupyter-notebooks/langgraph-agents/06_multi-agent-systems-middleware.ipynb) | Advanced middleware patterns for multi-agent orchestration |

---

## Topics covered in these notebooks

1. **Introduction to LangGraph**
   - State-based agent framework fundamentals
   - Graph architecture for agent workflows
   - Nodes, edges, and conditional routing

2. **Building Agents with LangGraph**
   - Creating simple agents with state management
   - Defining state schemas using `MessagesState`
   - Building and compiling graphs
   - Basic state management with reducers

3. **Tool Integration and Agent Capabilities**
   - Integrating external tools (search, APIs, databases)
   - Implementing conditional routing
   - Creating agent loops for multi-step reasoning
   - Tool calling and function execution

4. **Multi-Agent Systems**
   - Designing multi-agent workflows
   - Agent coordination and communication
   - Specialized agents for different tasks
   - Middleware for logging and monitoring

5. **Local vs Cloud LLM Options**
   - Using OpenAI API for cloud inference
   - Running locally with Ollama (Qwen2, Llama, Mistral)
   - Privacy and cost considerations
   - Model selection for different use cases

---

## Model Options

### Cloud Models (OpenAI)
- **GPT-4**: Best reasoning capabilities, production-ready
- **GPT-3.5-turbo**: Fast and cost-effective for most tasks

### Local Models (Ollama)

| Model | Size | Speed | Use Case |
|-------|------|-------|----------|
| `qwen2:0.5b` | 352MB | Very Fast | Simple tasks, learning, quick prototyping |
| `qwen2:1.5b` | ~1GB | Fast | Better reasoning, more complex tasks |
| `qwen2:7b` | ~4.7GB | Moderate | Production agents, complex reasoning |
| `llama3.2:1b` | ~1.3GB | Fast | Meta's efficient model |
| `mistral:7b` | ~4.1GB | Moderate | Strong reasoning capabilities |

Pull additional models:
```sh
ollama pull qwen2:1.5b
ollama pull llama3.2:1b
ollama pull mistral:7b
```

---
