# Scripts Directory

This directory contains all the Python modules and components used in the Chapter 6 Natural Language Pipelines project. The scripts are organized into logical modules for RAG (Retrieval Augmented Generation), evaluation, synthetic data generation, and analytics.

## 📁 Directory Structure

```
scripts/
├── README.md                           # This file
├── __init__.py                         # Python package initialization
├── elasticsearch_config.py             # Dual Elasticsearch configuration helper
├── validate_elasticsearch.py           # Elasticsearch connection validation
│
├── rag/                                # RAG System Components
│   ├── __init__.py
│   ├── indexing.py                     # Document indexing pipelines (single & dual embedding)
│   ├── hybridrag.py                    # Hybrid RAG system implementation
│   ├── naiverag.py                     # Basic RAG system implementation
│   └── pretty_print.py                 # Output formatting utilities
│
├── ragas_evaluation/                   # RAGAS Evaluation Framework
│   ├── __init__.py
│   └── ragasevalsupercomponent.py      # RAGAS evaluation super component
│
├── synthetic_data_generation/          # Synthetic Test Data Generation
│   ├── __init__.py
│   ├── synthetic_data_generator_supercomponent.py  # Main generator component
│   ├── synthetic_test_components.py    # Individual test generation components
│   ├── knowledge_graph_component.py    # Knowledge graph utilities
│   └── langchaindocument_component.py  # LangChain document processing
│
└── wandb_experiments/                  # Weights & Biases Analytics
    ├── __init__.py
    └── rag_analytics.py                # Enhanced RAG analytics with cost tracking
```

## 🧩 Component Overview

### Core Infrastructure

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `elasticsearch_config.py` | Elasticsearch setup | Dual instance configuration, connection helpers |
| `validate_elasticsearch.py` | Connection testing | Health checks, index validation |

### RAG Systems (`rag/`)

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `indexing.py` | Document indexing | Single/dual embedding support, multiple document types |
| `hybridrag.py` | Hybrid RAG system | BM25 + vector search, reranking, multiple retrievers |
| `naiverag.py` | Basic RAG system | Simple vector search implementation |
| `pretty_print.py` | Output formatting | Clean display of RAG results |

### Evaluation (`ragas_evaluation/`)

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `ragasevalsupercomponent.py` | RAG evaluation | RAGAS metrics, automated evaluation pipeline |

### Synthetic Data (`synthetic_data_generation/`)

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `synthetic_data_generator_supercomponent.py` | Main generator | Orchestrates synthetic test data creation |
| `synthetic_test_components.py` | Test components | Individual synthetic data generators |
| `knowledge_graph_component.py` | Knowledge graphs | Graph-based data generation |
| `langchaindocument_component.py` | Document processing | LangChain integration for document handling |

### Analytics (`wandb_experiments/`)

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `rag_analytics.py` | Cost & performance analytics | OpenAI pricing, embedding costs, W&B integration |

## 🚀 Usage Examples

### 1. Dual Elasticsearch Setup
```python
from scripts.elasticsearch_config import ElasticsearchConfig

# Get document stores for different embedding strategies
small_store = ElasticsearchConfig.get_small_document_store()
large_store = ElasticsearchConfig.get_large_document_store()
```

### 2. Document Indexing
```python
from scripts.rag.indexing import IndexingPipelineSuperComponent

# Single embedding indexing
indexing_sc = IndexingPipelineSuperComponent(
    document_store=small_store,
    embedder_model="text-embedding-3-small"
)
indexing_sc.run(urls=urls, sources=files)
```

### 3. Hybrid RAG System
```python
from scripts.rag.hybridrag import HybridRAGSuperComponent

# Initialize hybrid RAG with reranking
rag_sc = HybridRAGSuperComponent(
    document_store=large_store,
    embedder_model="text-embedding-3-large",
    reranker_model="BAAI/bge-reranker-base"
)
result = rag_sc.run(query="Your question here")
```

### 4. RAGAS Evaluation
```python
from scripts.ragas_evaluation.ragasevalsupercomponent import RAGEvaluationSuperComponent

# Evaluate RAG system performance
evaluator = RAGEvaluationSuperComponent(
    rag_supercomponent=rag_sc,
    system_name="hybrid-rag-test"
)
results = evaluator.run(csv_source="test_data.csv")
```

### 5. Cost Analytics
```python
from scripts.wandb_experiments.rag_analytics import RAGAnalytics

# Analyze costs and performance
analytics = RAGAnalytics(
    results=evaluation_results,
    model_name="gpt-4o-mini",
    embedding_models=["text-embedding-3-small", "text-embedding-3-large"]
)
summary = analytics.log_to_wandb(wandb_run)
```

## 🔧 Configuration Requirements

### Environment Variables
```bash
# OpenAI API Key (required for all components)
OPENAI_API_KEY=your_openai_api_key_here

# Weights & Biases API Key (required for analytics)
WANDB_API_KEY=your_wandb_api_key_here

# Elasticsearch URLs (configured in docker-compose.yml)
ES_SMALL_URL=http://localhost:9200
ES_LARGE_URL=http://localhost:9201
```

### Dependencies
- **Haystack**: Core RAG framework
- **RAGAS**: Evaluation metrics
- **Elasticsearch**: Vector database
- **OpenAI**: Embeddings and LLM
- **Weights & Biases**: Experiment tracking
- **LangChain**: Document processing utilities

## 📊 Integration with Notebooks

These scripts are designed to work seamlessly with the Jupyter notebooks in the parent directory:

- `add_observability_with_wandb.ipynb` → Uses `rag_analytics.py`, `ragasevalsupercomponent.py`
- `dual_elasticsearch_setup.ipynb` → Uses `elasticsearch_config.py`
- `elasticsearch_monitoring.ipynb` → Uses `elasticsearch_config.py`, `validate_elasticsearch.py`

## 🧪 Testing

Run tests from the project root:
```bash
# Run all tests
uv run pytest tests/

# Run specific component tests
uv run pytest tests/test_synthetic_test_components.py
uv run pytest tests/test_knowledge_graph_component.py
```

## 📈 Performance Considerations

- **Embedding Models**: `text-embedding-3-small` for speed, `text-embedding-3-large` for accuracy
- **Elasticsearch**: Separate instances optimize for different embedding sizes
- **Reranking**: Optional but improves retrieval quality at cost of latency
- **Cost Tracking**: All components include cost monitoring for production planning

## 🔄 Development Workflow

1. **Modify Components**: Update individual script files as needed
2. **Test Changes**: Run relevant tests to ensure compatibility
3. **Update Notebooks**: Reflect changes in notebook examples
4. **Document Updates**: Update this README for new features

## 📚 Related Documentation

- [Main Project README](../README.md) - Project overview and setup
- [Docker Compose Setup](../../docker-compose.yml) - Elasticsearch configuration
- [Project Configuration](../../pyproject.toml) - Dependencies and project metadata