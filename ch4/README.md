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
```

To obtain the API keys:
- OpenAI API key: Sign up at [OpenAI's platform](https://platform.openai.com)

7. **If you do not want to use OpenAI: Install Ollama for local LLM inference:**

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

**Get started learning about routers within pipelines**

| Notebook | Link | Description |
|---|---|---|
| ConditionalRouter | [conditional_router.ipynb](./jupyter-notebooks/routers/conditional_router.ipynb) | Build flexible routing logic with keyword-based and query classification |
| TextLanguageRouter | [text_language_router.ipynb](./jupyter-notebooks/routers/text_language_router.ipynb) | Implement multilingual pipelines with automatic language detection |
| MetadataRouter | [metadata_router.ipynb](./jupyter-notebooks/routers/metadata_router.ipynb) | Route documents based on metadata fields for advanced filtering |


**Apply routers within indexing, naive and hybrid RAG**

| Notebook | Link | Description |
|---|---|---|
| Indexing Pipeline | [indexing_pipeline.ipynb](./jupyter-notebooks/indexing_pipeline.ipynb) | Learn to build a pipeline for processing and indexing different document types |
| Semantic Search Pipeline | [semantic_search_pipeline.ipynb](./jupyter-notebooks/semantic_search_pipeline.ipynb) | Implement advanced semantic search capabilities using hybrid retrieval |
| Hybrid Pipeline | [hybrid_pipeline.ipynb](./jupyter-notebooks/hybrid_pipeline.ipynb) | Combine multiple retrieval methods for improved search accuracy |

**Multimodal RAG**

| Notebook | Link | Description |
|---|---|---|
| Image Embeddings with CLIP | [1_image_embeddings_with_clip.ipynb](./jupyter-notebooks/multimodal/1_image_embeddings_with_clip.ipynb) | Introduction to CLIP for image-text embeddings and similarity search |
| Multimodal Indexing with CLIP | [2_multimodal_indexing_clip.ipynb](./jupyter-notebooks/multimodal/2_multimodal_indexing_clip.ipynb) | Build indexing pipelines using CLIP embeddings (Approach 1) |
| Multimodal Indexing with LLM | [3_multimodal_indexing_llm.ipynb](./jupyter-notebooks/multimodal/3_multimodal_indexing_llm.ipynb) | Build indexing pipelines using LLM content extraction (Approach 2) |
| Multimodal RAG with Vision LLM | [4_multimodal_rag_vision_llm.ipynb](./jupyter-notebooks/multimodal/4_multimodal_rag_vision_llm.ipynb) | Complete RAG pipeline with vision LLM for image understanding |
| Audio Transcription with Whisper | [5_audio_transcription_whisper.ipynb](./jupyter-notebooks/multimodal/5_audio_transcription_whisper.ipynb) | Add audio transcription capabilities to multimodal RAG pipelines |

**Pipelines as supercomponents and Async pipelines**

| Notebook | Link | Description |
|---|---|---|
| Async Hybrid Pipeline | [async_hybrid_pipeline.ipynb](./jupyter-notebooks/async_hybrid_pipeline.ipynb) | Build asynchronous pipelines for improved performance |
| Supercomponents and Agentic RAG | [supercomponents_and_agentic_rag.ipynb](./jupyter-notebooks/supercomponents_and_agentic_rag.ipynb) | Create reusable pipeline components for complex workflows |

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

