# Chapter 6: Setting up a Reproducible Q&A Pipeline

This repository contains exercises and interactive notebooks for Chapter 6, focusing on building reproducible workflows for RAG systems using Elasticsearch, Haystack, and vector embeddings. You'll learn to implement and compare naive RAG vs hybrid RAG with reranking, incorporate observability with Weights and Biases, evaluate results with RAGAS, and optimize performance through feedback loops.

📚 **[Complete Chapter Overview](./chapter_overview.md)** - Comprehensive architectural guide covering SuperComponent patterns, evaluation frameworks, and experimental design.

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

**Preferred**: install [Docker Desktop](https://docs.docker.com/desktop/)

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
WANDB_API_KEY=your_wandb_key_here
```

To obtain the API keys:
- **OpenAI API key**: Sign up at [OpenAI's platform](https://platform.openai.com)
  - Navigate to [API Keys](https://platform.openai.com/api-keys)
  - Click "Create new secret key"
  - Copy the key and add it to your `.env` file
- **Weights & Biases API key**: Sign up at [Weights & Biases](https://wandb.ai)
  - Go to [User Settings → API Keys](https://wandb.ai/authorize)
  - Copy your API key and add it to your `.env` file
  - Required for experiment tracking and observability features

8. **Start Elasticsearch (Dual Instance Setup):**
	```bash
	# Start both Elasticsearch instances in detached mode
	docker-compose up -d
	```
	
	This starts two Elasticsearch instances:
	- **Small Instance** (Port 9200): Optimized for `text-embedding-3-small` (512MB-1GB heap)
	- **Large Instance** (Port 9201): Optimized for `text-embedding-3-large` (2GB-4GB heap)
	
	Verify both instances are running:
	```bash
	curl -s "localhost:9200/_cluster/health" | jq '.cluster_name'  # "es-small-cluster"
	curl -s "localhost:9201/_cluster/health" | jq '.cluster_name'  # "es-large-cluster"
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
Calculating embeddings: 1it [00:00,  1.03it/s]
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
curl -X GET "localhost:9200/small_embeddings/_count"
curl -X GET "localhost:9201/large_embeddings/_count"
```

```bash
# Expected output: {"count":26,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0}}%   
```

Get embeddings
```bash
# Sample a document to verify embeddings
curl -X GET "localhost:9200/small_embeddings/_search?size=1&pretty"
curl -X GET "localhost:9201/large_embeddings/_search?size=1&pretty"
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

📋 **[Chapter Overview](./chapter_overview.md)** - Detailed architectural guide covering SuperComponent patterns, evaluation frameworks, and experimental design

| Notebook | Link | Description |
|---|---|---|
| Getting Started with RAGAS Evaluation | [get_started_rag_evaluation_with_ragas.ipynb](./jupyter-notebooks/get_started_rag_evaluation_with_ragas.ipynb) | Comprehensive RAG system assessment using RAGAS framework with multiple evaluation metrics |
| RAGAS Evaluation with Custom Components | [ragas_evaluation_with_custom_components.ipynb](./jupyter-notebooks/ragas_evaluation_with_custom_components.ipynb) | Package evaluation through custom components and pipelines, and run evaluation on naive vs hybrid RAG with reranking |
| Adding Observability with Weights & Biases | [add_observability_with_wandb.ipynb](./jupyter-notebooks/add_observability_with_wandb.ipynb) | Integration of W&B for experiment tracking, performance monitoring, and RAG system observability |
| Synthetic Data Generation | [standalone_synthetic_data_generation.ipynb](./jupyter-notebooks/standalone_synthetic_data_generation.ipynb) | Automated test case creation and question-answer pair generation for evaluation datasets |

### RAG Pipeline Scripts

📁 **[Complete Scripts Documentation](./jupyter-notebooks/scripts/README.md)** - Comprehensive guide to all script components, usage examples, and architecture overview.

| Component | Link | Description |
|---|---|---|
| Document Indexing | [scripts/rag/indexing.py](./jupyter-notebooks/scripts/rag/indexing.py) | Multi-source data processing with dual embedding support and Elasticsearch integration |
| Naive RAG | [scripts/rag/naiverag.py](./jupyter-notebooks/scripts/rag/naiverag.py) | Basic retrieval-augmented generation with semantic search foundation |
| Hybrid RAG | [scripts/rag/hybridrag.py](./jupyter-notebooks/scripts/rag/hybridrag.py) | Advanced hybrid search combining keyword (BM25) and semantic search strategies |
| RAGAS Evaluation | [scripts/ragas_evaluation/](./jupyter-notebooks/scripts/ragas_evaluation/) | Automated RAG evaluation using RAGAS metrics |
| Elasticsearch Config | [scripts/elasticsearch_config.py](./jupyter-notebooks/scripts/elasticsearch_config.py) | Dual Elasticsearch instance configuration and helpers |
| W&B Analytics | [scripts/wandb_experiments/rag_analytics.py](./jupyter-notebooks/scripts/wandb_experiments/rag_analytics.py) | Enhanced cost tracking and performance analytics with current OpenAI pricing |
| Synthetic Data | [scripts/synthetic_data_generation/](./jupyter-notebooks/scripts/synthetic_data_generation/) | Automated test data generation for RAG evaluation |

---

## Pipeline Progression

The RAG evaluation notebooks and scripts are organized for comparative analysis:

### 1. Document Indexing Pipeline
- **Focus**: Multi-source data ingestion and processing for both RAG approaches
- **Components**: HTMLToDocument → PyPDFToDocument → DocumentSplitter → SentenceTransformersDocumentEmbedder → DocumentWriter (Elasticsearch)
- **Best for**: Learning the basics of document indexing and vector embeddings
- **Output**: Unified searchable document store with semantic embeddings for fair comparison

### 2. Naive RAG Baseline
- **Focus**: Simple retrieval-augmented generation with semantic search only
- **Components**: SentenceTransformersTextEmbedder → ElasticsearchEmbeddingRetriever → PromptBuilder → OpenAIGenerator
- **Best for**: Establishing baseline performance metrics for comparison
- **Output**: Direct answers using purely semantic retrieval

### 3. Hybrid RAG with Reranking
- **Focus**: Advanced retrieval combining keyword and semantic search with rank fusion
- **Components**: ElasticsearchBM25Retriever + ElasticsearchEmbeddingRetriever → RankFusion → PromptBuilder → OpenAIGenerator
- **Best for**: Demonstrating improved retrieval accuracy and answer quality
- **Output**: Enhanced answers with better context relevance through multi-strategy retrieval

---

## 🚀 Quick Reference

### Dual Elasticsearch Setup
- **Small Instance**: `localhost:9200` - Fast retrieval with `text-embedding-3-small`
- **Large Instance**: `localhost:9201` - High accuracy with `text-embedding-3-large`
- **Configuration**: See [elasticsearch_config.py](./jupyter-notebooks/scripts/elasticsearch_config.py)

### Current OpenAI Pricing (Built-in)
- **text-embedding-3-small**: $0.02 per 1M tokens
- **text-embedding-3-large**: $0.13 per 1M tokens  
- **gpt-4o-mini**: $0.15/$0.60 per 1M input/output tokens

### Key Commands
```bash
# Check document counts
curl "localhost:9200/small_embeddings/_count"
curl "localhost:9201/large_embeddings/_count"

# Start monitoring notebook
uv run jupyter lab jupyter-notebooks/elasticsearch_monitoring.ipynb

# Run cost analysis
uv run jupyter lab jupyter-notebooks/add_observability_with_wandb.ipynb
```

---

## Chapter Topics Covered

1. **Reproducible Workflow Building Blocks**
   - Setting up consistent environments with Docker and Elasticsearch
   - Version-controlled dependency management with uv
   - Containerized development workflows for fair RAG comparison

2. **Naive vs Hybrid RAG Implementation and Comparison**
   - Naive RAG: Semantic search-only retrieval implementation
   - Hybrid RAG: Keyword (BM25) + semantic search with reranking
   - Multi-source document processing (web content, PDFs) for both approaches

3. **Observability with Weights and Biases and Evaluating Results with RAGAS**
   - Performance monitoring and experiment tracking for RAG system comparison
   - Multi-dimensional RAG evaluation (faithfulness, relevance, context precision, recall)
   - **Enhanced cost analytics** with current OpenAI pricing (November 2024)
   - **Dual embedding comparison** (`text-embedding-3-small` vs `text-embedding-3-large`)
   - Comprehensive cost breakdown including LLM and embedding operations
   - Automated evaluation pipeline setup for systematic comparison

4. **Performance Optimization through Feedback Loops**
   - Iterative improvement cycles using RAGAS evaluation results
   - Custom evaluation metrics for comparing retrieval strategies
   - Performance benchmarking between naive and hybrid RAG systems
   - Reranking optimization strategies based on evaluation feedback





