# Chapter 4: Building Advanced Haystack Pipelines

This repository contains exercises and interactive notebooks for Chapter 4, focusing on building advanced pipelines with Haystack for different use cases.

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
4. **(Recommended) Open this `ch4` folder in a new VS Code window.**
5. **Select the virtual environment as the Jupyter kernel:**
	- Open any notebook.
	- Click the kernel picker (top right) and select the `.venv` environment.

6. **Set up API keys:**

Create a `.env` file in the root directory with your API keys:
```sh
OPENAI_API_KEY=your_openai_key_here
SERPER_API_KEY=your_serper_key_here
```

To obtain the API keys:
- OpenAI API key: Sign up at [OpenAI's platform](https://platform.openai.com)
- Serper API key: Register at [Serper.dev](https://serper.dev)

---

## Contents

| Notebook | Link | Description |
|---|---|---|
| Indexing Pipeline | [indexing_pipeline.ipynb](./jupyter-notebooks/indexing_pipeline.ipynb) | Learn to build a pipeline for processing and indexing different document types |
| Semantic Search Pipeline | [semantic_search_pipeline.ipynb](./jupyter-notebooks/semantic_search_pipeline.ipynb) | Implement advanced semantic search capabilities using hybrid retrieval |
| Hybrid Pipeline | [hybrid_pipeline.ipynb](./jupyter-notebooks/hybrid_pipeline.ipynb) | Combine multiple retrieval methods for improved search accuracy |
| Supercomponents and advanced agentic RAG | [supercomponents_and_agentic_rag.ipynb](./jupyter-notebooks/supercomponents_and_agentic_rag.ipynb) | Create reusable pipeline components for complex workflows |

Images for pipeline visualizations are in `jupyter-notebooks/images/`.

---

## Chapter topics covered

1. Designing a pipeline with Haystack’s design in mind 
2. Building pipelines with Haystack 
* Preprocessing pipelines: Leveraging information from the internet, text and tabular information 
* Indexing pipelines 
* Question and answer pipelines 
* Routers in pipelines
3. Sample pipeline use cases 
4. Indexing and Naive Retrieval Augmented Generation 
5. Advanced pipeline use cases 
6. Hybrid Retrieval Augmented Generation with Reranking and evaluation 
7. Supercomponents: Pipelines as tools for agents 

