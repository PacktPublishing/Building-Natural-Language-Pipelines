# Chapter 2: Your First AI Agents

This repository contains beginner-friendly notebooks for Chapter 2, introducing you to building AI agents that can think, use tools, and answer questions.

## Setup Instructions

1. **Install [uv](https://github.com/astral-sh/uv):**
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

Create a `.env` file in the `jupyter-notebooks/` directory with your API key:
```sh
TAVILY_API_KEY=your_tavily_key_here
```

To obtain the API key:
- Tavily API key: Register at [Tavily](https://tavily.com) (free tier available for learning)

7. **Install Ollama for local LLM inference:**

```sh
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from: https://ollama.com
```

Pull the Mistral-Nemo model:
```sh
ollama pull mistral-nemo:12b
```

Pull Nomic embedding model:
```sh
ollama pull nomic-embed-text
```

---

## Contents

### Beginner Notebooks

| Notebook | Link | Description |
|---|---|---|
| **01** Interactive Prompting with Ollama | [01_prompt-ollama-model.ipynb](./jupyter-notebooks/01_prompt-ollama-model.ipynb) | 🔌 Prompt Mistral-Nemo locally with Ollama |
| **02** Your First Agent | [02_create-simple-agent.ipynb](./jupyter-notebooks/02_create-simple-agent.ipynb) | 🎯 Build your first AI agent with tools and memory |
| **03** Document Q&A with LangChain | [03_document-qa-langchain.ipynb](./jupyter-notebooks/03_document-qa-langchain.ipynb) | 📚 Build a retrieval-augmented Document Q&A pipeline |

### Advanced: LangChain & LangGraph

| Notebook | Link | Description |
|---|---|---|
| **02** Middleware Tutorial | [02_middleware-tutorial.ipynb](./jupyter-notebooks/advanced-langchain-langgraph/02_middleware-tutorial.ipynb) | Understanding middleware patterns in LangGraph |
| **03** Multi-Agent Workflow | [03_multi-agent-workflow.ipynb](./jupyter-notebooks/advanced-langchain-langgraph/03_multi-agent-workflow.ipynb) | Coordinate multiple agents in workflows |
| **04** Understanding State Graph | [04_understanding-state-graph.ipynb](./jupyter-notebooks/advanced-langchain-langgraph/04_understanding-state-graph.ipynb) | Build state machines with LangGraph |
| **05** Graph-Based Agent with Tools | [05_graph-based-agent-with-tools.ipynb](./jupyter-notebooks/advanced-langchain-langgraph/05_graph-based-agent-with-tools.ipynb) | Create agents using state graphs and tools |
| **06** Multi-Agent Systems Middleware | [06_multi-agent-systems-middleware.ipynb](./jupyter-notebooks/advanced-langchain-langgraph/06_multi-agent-systems-middleware.ipynb) | Advanced multi-agent coordination patterns with middleware |

---

## What You'll Learn

### 1. **Interactive Prompting with Ollama**
   - Direct prompting of LLMs using LangChain
   - Using ChatOllama for local model inference
   - Understanding temperature and its effects
   - Building conversational exchanges with message history
   - Experimenting with different prompting techniques

### 2. **Your First AI Agent**
   - What agents are and how they work
   - Creating agents with `create_agent()`
   - Giving agents tools (like web search)
   - Understanding when agents use tools vs. direct answers
   - Conversation memory basics

### 3. **Document Q&A with LangChain**
   - Loading and processing documents
   - Splitting documents into chunks for retrieval
   - Creating embeddings with Ollama (nomic-embed-text)
   - Building vector stores with FAISS
   - Implementing semantic similarity search
   - Creating retrieval-augmented generation (RAG) pipelines
   - Combining retrievers with LLMs for question answering

### 4. **Running Everything Locally**
   - Using Ollama for privacy and cost savings
   - Running Mistral-Nemo locally
   - When to use local vs. cloud models
   - Setting up local embeddings for RAG

### 5. **Advanced: LangGraph & Multi-Agent Systems**
   - Understanding LangGraph state machines and graphs
   - Building middleware for agent coordination
   - Creating multi-agent workflows and collaboration patterns
   - Using state graphs to control agent behavior
   - Implementing graph-based agents with tools
   - Advanced multi-agent system architectures

---

## Model Recommendations

### For This Chapter

**Recommended: Mistral-Nemo (Local with Ollama)**
- **Size**: ~7GB
- **Speed**: Fast on modern laptops
- **Benefits**: 
  - ✅ Free to use
  - ✅ Runs completely locally (privacy)
  - ✅ Great for learning
  - ✅ Good tool-calling support


### Why Local Models?
- 💰 **No API costs** - Learn without worrying about bills
- 🔒 **Privacy** - Your data stays on your machine
- ⚡ **Always available** - No internet required after download
- 🎓 **Perfect for learning** - Experiment freely!

---
