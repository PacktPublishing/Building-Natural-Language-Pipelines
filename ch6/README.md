# Chapter 6: Setting up a Reproducible Q&A Pipeline

This repository contains exercises and interactive notebooks for Chapter 6, focusing on building reproducible workflows for RAG systems using Elasticsearch, Haystack, and vector embeddings. You'll learn to implement and compare naive RAG vs hybrid RAG with reranking, incorporate observability with Weights and Biases, evaluate results with RAGAS, and optimize performance through feedback loops.

## Table of Contents

- [Setup Instructions](#setup-instructions)
  - [Elasticsearch Document Indexing Workflow](#elasticsearch-document-indexing-workflow)
    - [Step 1: Prepare Data Sources](#step-1-prepare-data-sources)
    - [Step 2: Generate Synthetic Data](#step-2-generate-synthetic-data)
    - [Step 3: Run the Indexing Pipeline](#step-3-run-the-indexing-pipeline)
    - [Step 4: Verify Documents are Loaded](#step-4-verify-documents-are-loaded)
    - [Step 5: Clean Up (Optional)](#step-5-clean-up-optional)
  - [Troubleshooting](#troubleshooting)
- [Contents](#contents)
  - [RAG Pipeline Scripts](#rag-pipeline-scripts)
- [Pipeline Progression](#pipeline-progression)
- [Chapter Topics Covered](#chapter-topics-covered)

## Setup Instructions

1. **Install Docker:**
	```bash
	brew install docker
	brew install docker-compose
	brew install --cask docker
	```

2. **Install [uv](https://github.com/astral-sh/uv):**
	```sh
	pip install uv
	```
3. **Install dependencies:**
	```sh
	uv sync
	```
4. **Activate the virtual environment:**
	```sh
	source .venv/bin/activate
	```
5. **(Recommended) Open this `ch6` folder in a new VS Code window.**
6. **Select the virtual environment as the Jupyter kernel:**
	- Open any notebook.
	- Click the kernel picker (top right) and select the `.venv` environment.

7. **Set up API keys:**

Create a `.env` file in the root directory with your API keys:
```sh
OPENAI_API_KEY=your_openai_key_here
```

To obtain the API key:
- OpenAI API key: Sign up at [OpenAI's platform](https://platform.openai.com)

8. **Start Elasticsearch:**
	```bash
	# Start in detached mode
	docker-compose up -d
	```

### Elasticsearch Document Indexing Workflow

Now you'll index multiple data sources with vector embeddings for semantic search.

#### Step 1: Prepare Data Sources

The indexing pipeline processes four types of data sources:

1. **Web content**: Fetches from 
- `https://www.bbc.com/news/articles/c2l799gxjjpo`
- `https://www.brookings.edu/articles/how-artificial-intelligence-is-transforming-the-world/`
2. **PDF file**: `data_for_indexing/howpeopleuseai.pdf` 

#### Step 2: Generate Synthetic Data

Execute

```bash
cd jupyter-notebooks
uv run python scripts/synthetic_data_generation/sdg_html_pdf.py
```

This will create a file under [jupyter-notebooks/data-for-eval/](./jupyter-notebooks/data_for_eval/)

[A sample is provided here](./jupyter-notebooks/data_for_eval/synthetic_tests_advanced_branching_50.csv)

#### Step 3: Run the Indexing Pipeline

Execute the indexing script to process all data sources and store them in Elasticsearch:

```bash
cd jupyter-notebooks
uv run python scripts/rag/indexing.py
```

**Expected Output:**
```
Processing web URL: ['https://www.bbc.com/news/articles/c2l799gxjjpo', 'https://www.brookings.edu/articles/how-artificial-intelligence-is-transforming-the-world/']
Batches: 100%|███████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:01<00:00,  4.42it/s]
Indexing completed successfully!
```

Verify the ElasticSearch store was populated

```bash
curl -X GET "localhost:9200/_cat/health?v"
```

The pipeline will:
- Fetch and process web content from the Haystack blog
- Convert and chunk the PDF document into readable segments
- Generate 384-dimensional vector embeddings for all content

#### Step 4: Verify Documents are Loaded

Check that documents have been successfully indexed:

```bash
# Get total document count
curl -X GET "localhost:9200/default/_count"

# Expected output: {"count":10,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0}}% 

# View document breakdown by source
curl -X GET "localhost:9200/default/_search?size=0&pretty" -H "Content-Type: application/json" -d '{
  "aggs": {
    "sources": {
      "terms": {
        "field": "file_path.keyword", 
        "size": 10,
        "missing": "web_content"
      }
    }
  }
}'

# Sample a document to verify embeddings
curl -X GET "localhost:9200/default/_search?size=1&pretty"
```

#### Step 5: Clean Up (Optional)

To stop the Elasticsearch container and clean up:

```bash
# Stop the container
docker-compose down

# Remove the index (if you want to start fresh)
curl -X DELETE "localhost:9200/default"
```

### Troubleshooting

**Issue: PDF not found warnings**
- Ensure you're running from the correct directory
- Verify the PDF file exists in `data_for_indexing/howpeopleuseai.pdf`

---

## Contents

| Notebook | Link | Description |
|---|---|---|
| RAGAS Evaluation Tutorial | [rag_evaluation_with_ragas.ipynb](./jupyter-notebooks/rag_evaluation_with_ragas.ipynb) | Comprehensive RAG system assessment using RAGAS framework with multiple evaluation metrics |
| Custom Evaluation Methods | [rag_evaluation_custom.ipynb](./jupyter-notebooks/rag_evaluation_custom.ipynb) | Custom evaluation components and tailored assessment criteria for performance analysis |
| Synthetic Data Generation | [standalone_synthetic_data_generation.ipynb](./jupyter-notebooks/standalone_synthetic_data_generation.ipynb) | Automated test case creation and question-answer pair generation for evaluation datasets |

### RAG Pipeline Scripts

| Component | Link | Description |
|---|---|---|
| Document Indexing | [scripts/rag/indexing.py](./jupyter-notebooks/scripts/rag/indexing.py) | Multi-source data processing with vector embedding generation and Elasticsearch integration |
| Naive RAG | [scripts/rag/naiverag.py](./jupyter-notebooks/scripts/rag/naiverag.py) | Basic retrieval-augmented generation with semantic search foundation |
| Hybrid RAG | [scripts/rag/hybridrag.py](./jupyter-notebooks/scripts/rag/hybridrag.py) | Advanced hybrid search combining keyword (BM25) and semantic search strategies |

---

## Pipeline Progression

The Q&A system notebooks and scripts are organized in increasing complexity:

### 1. Document Indexing Pipeline
- **Focus**: Multi-source data ingestion and processing
- **Components**: HTMLToDocument → PyPDFToDocument → DocumentSplitter → SentenceTransformersDocumentEmbedder → DocumentWriter (Elasticsearch)
- **Best for**: Learning the basics of document indexing and vector embeddings
- **Output**: Searchable document store with semantic embeddings

### 2. Naive RAG System
- **Focus**: Simple question-answering with semantic search
- **Components**: SentenceTransformersTextEmbedder → ElasticsearchEmbeddingRetriever → PromptBuilder → OpenAIGenerator
- **Best for**: Understanding basic RAG architecture and retrieval mechanics
- **Output**: Direct answers from document context

### 3. Hybrid RAG System
- **Focus**: Advanced retrieval combining keyword and semantic search
- **Components**: ElasticsearchBM25Retriever + ElasticsearchEmbeddingRetriever → RankFusion → PromptBuilder → OpenAIGenerator
- **Best for**: Production-ready systems requiring high retrieval accuracy
- **Output**: Enhanced answers with improved context relevance

---

## Chapter Topics Covered

1. **Reproducible Workflow Building Blocks**
   - Setting up consistent environments with Docker and Elasticsearch
   - Version-controlled dependency management with uv
   - Containerized development workflows

2. **Setting up Q&A Pipelines**
   - Case I: Q&A system for small collection of text
   - Case II: Q&A system for complex knowledge bases
   - Multi-source document processing (web content, PDFs)

3. **Incorporating Observability with Weights and Biases and Evaluating Results with RAGAS**
   - Performance monitoring and experiment tracking
   - Multi-dimensional RAG evaluation (faithfulness, relevance, context precision)
   - Automated evaluation pipeline setup

4. **Optimising Performance through Feedback Loops**
   - Iterative improvement cycles using evaluation results
   - Custom evaluation metrics and components
   - Performance benchmarking and optimization strategies





