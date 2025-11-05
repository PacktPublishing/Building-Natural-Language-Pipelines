# Building RAG Applications with Haystack 2.0

Supplementary material for the book *"Building Natural Language Pipelines"* published by Packt

Author: Laura Funderburk

## Table of Contents

- [What You'll Learn to Build](#what-youll-learn-to-build)
- [Setting Up](#setting-up)
- [Chapter Breakdown](#chapter-breakdown)
  - [Chapter 3: Introduction to Haystack](#chapter-3-introduction-to-haystack)
  - [Chapter 4: Bringing components together: Haystack pipelines for different use cases](#chapter-4-bringing-components-together-haystack-pipelines-for-different-use-cases)
  - [Chapter 5: Haystack pipeline development with custom components](#chapter-5-haystack-pipeline-development-with-custom-components)
  - [Chapter 6: Setting up a reproducible project: naive vs hybrid RAG with reranking and evaluation](#chapter-6-setting-up-a-reproducible-project-naive-vs-hybrid-rag-with-reranking-and-evaluation)
  - [Chapter 7: Production deployment strategies](#chapter-7-production-deployment-strategies)


## What You'll Learn to Build

This book guides you through building advanced **Retrieval-Augmented Generation (RAG)** with evaluation using the [Haystack 2.0](https://haystack.deepset.ai/), [Ragas](https://docs.ragas.io/en/stable/) and [LangGraph](https://www.langchain.com/langgraph) frameworks. Starting with NLP fundamentals, you'll progress through creating intelligent search systems, custom components, and production-ready applications. The journey culminates in deploying scalable RAG solutions with proper evaluation frameworks, containerized deployments, and real-world projects including financial document analysis, legal chatbots, and text classification systems.

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

### **[Chapter 6: Setting up a reproducible project: naive vs hybrid RAG with reranking and evaluation](./ch6/)**
**Reproducible Workflows & Evaluation**
- **Reproducible Workflow Building Blocks**: Setting up consistent environments with Docker, Elasticsearch, and dependency management
- **Naive RAG Implementation**: Building basic retrieval-augmented generation with semantic search
- **Hybrid RAG with Reranking**: Advanced retrieval combining keyword (BM25) and semantic search with rank fusion strategies
- **Evaluation with RAGAS**: Using the RAGAS framework to assess and compare naive vs hybrid RAG system quality across multiple dimensions
- **Observability with Weights and Biases**: Implementing monitoring and tracking for RAG system performance comparison and experiment management
- **Performance Optimization through Feedback Loops**: Creating iterative improvement cycles using evaluation results to enhance retrieval and generation performance

### **Chapter 7: Production deployment strategies**
**Deployment & Scaling**

#### **[Deploying a Retriever Pipeline as FastAPI App](./ch7/)**
- **FastAPI REST API**: Building production-ready APIs with clean documentation and error handling
- **Docker Containerization**: Full containerization with Docker Compose for scalable deployments
- **Elasticsearch Integration**: Production-grade document storage and hybrid search capabilities
- **Local Development Workflows**: Script-based development environment setup and testing

#### **[Deploying Multiple Pipelines with Hayhooks](./ch7-hayhooks/)**
- **Hayhooks Framework**: Multi-pipeline deployment using Haystack's native REST API framework
- **Pipeline Orchestration**: Managing multiple RAG pipelines (indexing + querying) as microservices
- **Service Discovery**: Automated API endpoint generation and pipeline management
- **Production Scaling**: Container-based deployment strategies for enterprise environments

