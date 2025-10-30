# Building RAG Applications with Haystack 2.0

Supplementary material for the book *"Building Natural Language Pipelines"* published by Packt

Author: Laura Funderburk

## What You'll Learn to Build

This book guides you through building advanced **Retrieval-Augmented Generation (RAG)** with evaluation using the [Haystack 2.0](https://haystack.deepset.ai/), [Ragas](https://docs.ragas.io/en/stable/) and [LangGraph](https://www.langchain.com/langgraph) frameworks. Starting with NLP fundamentals, you'll progress through creating intelligent search systems, custom components, and production-ready applications. The journey culminates in deploying scalable RAG solutions with proper evaluation frameworks, containerized deployments, and real-world projects including financial document analysis, legal chatbots, and text classification systems.

## Chapter breakdown

### **[Chapter 3: Introduction to Haystack](./ch3/)**
**Core Concepts & Foundation**
- **Component Architecture**: Understanding Haystack's modular design patterns
- **Pipeline Construction**: Building linear and branching data flow pipelines  
- **Document Processing**: Text extraction, cleaning, and preprocessing workflows
- **Prompting LLMs**: Learn to build prompt templates and guide how an LLM responds
- **Package pipelines as Supercomponents**: Abstract a pipeline as a Haystack component

### **[Chapter 4: Bringing components together: Haystack pipelines for different use cases](./ch4/)**
**Scaling & Optimization**
- **Indexing Pipelines**: Automated document ingestion and preprocessing workflows
- **Naive RAG**: Semantic search using sentence transformers and embedding models
- **Hybrid RAG**: Combining keyword (BM25) and semantic (vector) search strategies
- **Reranking and RAG fusion**: Advanced retrieval techniques using reranking
- **Pipelines as tools for an Agent**: Package advanced RAG as a tool for an autonomous Agent

### **[Chapter 5: Haystack pipeline development with custom components](./ch5/)**
**Extensibility & Testing**
- **Component SDK**: Creating custom Haystack components with proper interfaces
- **Knowledge Graph Integration**: Building components for structured knowledge representation
- **Synthetic Data Generation**: Automated test data creation for pipeline validation
- **Quality Control Systems**: Implementing automated evaluation and monitoring components
- **Unit Testing Frameworks**: Comprehensive testing strategies for custom components


## Setting up

Clone the repository

```bash
git clone https://github.com/PacktPublishing/Building-Natural-Language-Pipelines.git

cd Building-Natural-Language-Pipelines/

```

Each chapter contains a `pyproject.toml` file with the folder's dependencies. **(Recommended) Open each folder in a new VS Code window.**

1. **Install [uv](https://github.com/astral-sh/uv):**
	```sh
	pip install uv
	```
2. **Change directories into the folder**
3. **Install dependencies:**
	```sh
	uv sync
	```
4. **Activate the virtual environment:**
	```sh
	source .venv/bin/activate
	```
5. **Select the virtual environment as the Jupyter kernel:**
	- Open any notebook.
	- Click the kernel picker (top right) and select the `.venv` environment.

---
