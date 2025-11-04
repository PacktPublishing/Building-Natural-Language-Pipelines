# Chapter 6: Advanced RAG Architecture with SuperComponents and Comprehensive Evaluation

## Overview

This chapter demonstrates how to transform traditional RAG pipelines into modular, reusable SuperComponents and establish comprehensive evaluation workflows using RAGAS and Weights & Biases (W&B). You'll learn to build scalable RAG systems that can be systematically compared, optimized, and tracked for performance improvements.

## Table of Contents

1. [Core Architectural Concepts](#core-architectural-concepts)
2. [SuperComponent Abstraction Pattern](#supercomponent-abstraction-pattern)
3. [RAG Pipeline Implementations](#rag-pipeline-implementations)
4. [Evaluation Framework Architecture](#evaluation-framework-architecture)
5. [Experimental Design and Analytics](#experimental-design-and-analytics)
6. [Dependencies and Environment Setup](#dependencies-and-environment-setup)
7. [Key Assumptions and Reproducibility](#key-assumptions-and-reproducibility)
8. [Complete Workflow Guide](#complete-workflow-guide)

---

## Core Architectural Concepts

### The SuperComponent Pattern

**SuperComponents** are Haystack's solution for creating reusable, composable pipeline architectures. They encapsulate complex multi-step processes into single, manageable units that can be:

- **Configured once, used many times**: Consistent behavior across experiments
- **Easily swapped**: Compare different RAG approaches with identical evaluation conditions
- **Systematically evaluated**: Standard interfaces enable automated comparison
- **Scaled horizontally**: Run multiple configurations simultaneously

### Key Design Principles

1. **Separation of Concerns**: Each SuperComponent handles one major workflow (indexing, retrieval, evaluation)
2. **Standardized Interfaces**: Consistent input/output patterns enable interoperability  
3. **Configuration Externalization**: Model parameters, API keys, and settings are injectable
4. **Pipeline Composition**: SuperComponents can be chained for complex workflows
5. **Evaluation Integration**: Built-in hooks for metrics collection and analysis

### Dual Elasticsearch Architecture

This chapter implements a **dual instance architecture** optimized for embedding model comparison:

**Architecture Overview**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Dual Elasticsearch Setup                 │
├─────────────────────────────────────────────────────────────┤
│  Small Instance (Port 9200)     │  Large Instance (Port 9201) │
│  ├─ Heap: 1GB                  │  ├─ Heap: 4GB                │
│  ├─ Index: "small_embeddings"   │  ├─ Index: "large_embeddings" │
│  ├─ Model: text-embedding-3-small │ ├─ Model: text-embedding-3-large │
│  ├─ Dimensions: 1536            │  ├─ Dimensions: 3072           │
│  ├─ Cost: $0.02/1M tokens      │  ├─ Cost: $0.13/1M tokens     │
│  └─ Use Case: Fast, cost-effective │ └─ Use Case: Maximum accuracy │
└─────────────────────────────────────────────────────────────┘
```

**Key Benefits**:
- **Parallel Evaluation**: Run identical experiments on both embedding models simultaneously
- **Resource Optimization**: Each instance optimized for its embedding model's requirements  
- **Cost Analysis**: Direct comparison of performance vs cost trade-offs
- **Infrastructure Scaling**: Independent scaling based on workload requirements
- **Fair Comparison**: Identical data, identical conditions, different embedding approaches

---

## SuperComponent Abstraction Pattern

### Base Structure

All SuperComponents in this architecture follow a consistent pattern:

```python
@super_component
class ExampleSuperComponent:
    def __init__(self, configuration_parameters):
        # Store configuration
        # Validate requirements (API keys, models, etc.)
        self._build_pipeline()
    
    def _build_pipeline(self):
        # 1. Initialize individual components
        # 2. Create Pipeline instance  
        # 3. Add components to pipeline
        # 4. Connect components (define data flow)
        # 5. Define input/output mappings
```

### Input/Output Mapping Strategy

SuperComponents use explicit input and output mappings to create clean interfaces:

```python
# Input mapping: external inputs → internal component inputs
self.input_mapping = {
    "query": ["text_embedder.text", "retriever.query", "prompt_builder.question"]
}

# Output mapping: internal component outputs → external outputs  
self.output_mapping = {
    "llm.replies": "replies",
    "retriever.documents": "documents"
}
```

This pattern enables:
- **Interface Abstraction**: External users don't need to know internal component names
- **Easy Substitution**: Change internal implementation without breaking external usage
- **Parallel Processing**: Map single inputs to multiple components simultaneously

---

## RAG Pipeline Implementations

### 1. Indexing Pipeline SuperComponent

**Purpose**: Transform diverse content sources into searchable document stores

**Architecture**:
```
URLs/Files → FileTypeRouter → [PDF|HTML|Text]Converter → DocumentJoiner → 
Preprocessor → OpenAIDocumentEmbedder → DocumentWriter → ElasticsearchDocumentStore
```

**Key Features**:
- **Multi-format Support**: PDFs, HTML, plain text, web URLs
- **Smart Routing**: Automatic content type detection and appropriate processing
- **Configurable Preprocessing**: Sentence splitting, overlap control, cleaning
- **Embedding Flexibility**: Configurable OpenAI embedding models
- **Batch Processing**: Efficient handling of large document collections

**Dual Configuration for Embedding Model Comparison**:
```python
# Small embeddings configuration (fast, cost-effective)
small_embeddings_store = ElasticsearchDocumentStore(
    hosts="http://localhost:9200", 
    index="small_embeddings"
)
indexing_small_sc = IndexingPipelineSuperComponent(
    document_store=small_embeddings_store,
    embedder_model="text-embedding-3-small",  # 1536-dim, $0.02/1M tokens
    openai_api_key=api_key
)

# Large embeddings configuration (high accuracy)
large_embeddings_store = ElasticsearchDocumentStore(
    hosts="http://localhost:9201", 
    index="large_embeddings"
)
indexing_large_sc = IndexingPipelineSuperComponent(
    document_store=large_embeddings_store,
    embedder_model="text-embedding-3-large",  # 3072-dim, $0.13/1M tokens
    openai_api_key=api_key
)
```

### 2. Naive RAG SuperComponent

**Purpose**: Baseline RAG implementation using simple vector similarity retrieval

**Architecture**:
```
Query → OpenAITextEmbedder → ElasticsearchEmbeddingRetriever → 
PromptBuilder → OpenAIGenerator → Response
```

**Design Characteristics**:
- **Simplicity**: Single retrieval method (dense vector search)
- **Speed**: Fast retrieval and generation
- **Baseline**: Establishes performance floor for comparisons
- **Consistent Prompting**: Standardized prompt template with context injection

**Prompt Template**:
```jinja2
Given the following information, answer the question.

Context:
{% for doc in documents %}
{{ doc.content }}
{% endfor %}

Question: {{question}}
Answer:
```

### 3. Hybrid RAG SuperComponent

**Purpose**: Advanced RAG using dual retrieval methods and re-ranking

**Architecture**:
```
Query → [OpenAITextEmbedder + ElasticsearchBM25Retriever] → 
DocumentJoiner → SentenceTransformersSimilarityRanker → 
PromptBuilder → OpenAIGenerator → Response
```

**Advanced Features**:
- **Dual Retrieval**: Dense (semantic) + sparse (BM25) retrieval
- **Document Joining**: Combines results from multiple retrieval methods
- **Re-ranking**: Cross-encoder model for precision improvement
- **Configurable Components**: Flexible embedding, ranking, and LLM models

**Performance Benefits**:
- **Recall**: BM25 catches exact keyword matches
- **Precision**: Semantic embedding finds conceptually similar content  
- **Ranking**: Cross-encoder provides final relevance ordering
- **Robustness**: Multiple retrieval strategies reduce failure modes

---

## Evaluation Framework Architecture

### RAGAS Integration Pattern

The evaluation framework uses a multi-stage pipeline approach:

```
Evaluation Dataset → RAG SuperComponent → Response Augmentation → 
RAGAS Metrics Calculation → Results Analysis
```

### Core Evaluation Components

#### 1. CSVReaderComponent
```python
@component
class CSVReaderComponent:
    """Loads evaluation datasets from CSV files with standard schema"""
```
- **Expected Schema**: `question`, `ground_truth`, `contexts` columns
- **Flexible Loading**: Supports various CSV formats and encodings
- **Validation**: Ensures required columns are present

#### 2. RAGDataAugmenterComponent  
```python
@component  
class RAGDataAugmenterComponent:
    """Processes evaluation queries through RAG SuperComponents"""
```
- **SuperComponent Integration**: Accepts any RAG SuperComponent
- **Batch Processing**: Efficiently handles entire evaluation datasets
- **Context Extraction**: Captures retrieved documents for context-based metrics
- **Response Collection**: Gathers generated answers for evaluation

#### 3. RagasEvaluationComponent
```python
@component
class RagasEvaluationComponent:
    """Computes RAGAS metrics on augmented evaluation data"""
```

**Metrics Calculated**:
- **Faithfulness**: Response alignment with retrieved context
- **Factual Correctness**: Accuracy compared to ground truth
- **Context Recall**: Retrieval system's ability to find relevant information  
- **Response Relevancy**: Answer's direct relevance to the question

### RAGEvaluationSuperComponent

**Complete Evaluation Pipeline**:
```python
@super_component
class RAGEvaluationSuperComponent:
    """Systematic RAG comparison framework"""
```

**Pipeline Flow**:
```
CSV Source → CSVReader → RAGDataAugmenter → RagasEvaluation → 
Metrics & Detailed Results
```

**Key Benefits**:
- **Consistent Conditions**: Same evaluation dataset and conditions for all RAG systems
- **Comprehensive Metrics**: Multiple evaluation dimensions  
- **Reproducible**: Deterministic evaluation process
- **Scalable**: Easy addition of new RAG implementations

---

## Experimental Design and Analytics

### Weights & Biases Integration

**RAGAnalytics Class**: Comprehensive cost and performance tracking

```python
class RAGAnalytics:
    """Enhanced analytics with cost tracking and W&B integration"""
```

**Analytics Capabilities**:
1. **Cost Calculation**: 
   - Token usage tracking (input/output)
   - Current OpenAI pricing integration
   - Embedding cost analysis
   - Total experiment cost estimation

2. **Performance Metrics**:
   - RAGAS metric aggregation
   - Statistical significance testing
   - Performance improvement quantification
   - Stability analysis (standard deviations)

3. **W&B Logging**:
   - Experiment configuration tracking
   - Metric time series
   - Cost progression monitoring  
   - Model comparison dashboards

### Experimental Configurations

#### Naive vs Hybrid Comparison
```python
# Configuration for systematic comparison
naive_config = {
    "embedder_model": "text-embedding-3-small",
    "llm_model": "gpt-4o-mini", 
    "top_k": 3
}

hybrid_config = {
    "embedder_model": "text-embedding-3-small",
    "llm_model": "gpt-4o-mini",
    "top_k": 3,
    "ranker_model": "BAAI/bge-reranker-base"
}
```

#### Embedding Model Ablation Study  
```python
# Small vs Large embedding comparison
small_embedding_config = {
    "embedder_model": "text-embedding-3-small",  # $0.02/1M tokens
    "llm_model": "gpt-4o-mini"
}

large_embedding_config = {
    "embedder_model": "text-embedding-3-large",   # $0.13/1M tokens  
    "llm_model": "gpt-4o-mini"
}
```

### Performance Analysis Framework

**Statistical Comparison**:
```python
def create_comparison_report(naive_results, hybrid_results):
    """Generate comprehensive comparison analysis"""
    # Metric-by-metric comparison
    # Statistical significance testing
    # Cost-benefit analysis
    # Stability assessment
```

**Key Analysis Dimensions**:
- **Effectiveness**: Which approach performs better on each metric?
- **Efficiency**: Cost per query analysis
- **Stability**: Performance variance across evaluation samples  
- **Trade-offs**: Performance gains vs computational costs

---

## Dependencies and Environment Setup

### Core Dependencies

**Pipeline Framework**:
```toml
"haystack-ai>=2.19.0"           # Core pipeline framework
"elasticsearch-haystack>=4.1.0"  # Elasticsearch integration
```

**RAG Components**:  
```toml
"sentence-transformers>=5.0.0"   # Embedding models and re-rankers
"transformers>=4.57.1"          # Transformer models
```

**Evaluation Framework**:
```toml
"ragas>=0.3.7"                  # RAGAS evaluation framework
"ragas-haystack>=1.0.0"         # Haystack-RAGAS integration
```

**Data Processing**:
```toml
"langchain-community>=0.4"      # Document loaders and utilities
"langchain-openai>=1.0.1"      # OpenAI integrations
"pymupdf>=1.26.5"              # PDF processing
"trafilatura>=2.0.0"           # Web content extraction
```

**Analytics and Tracking**:
```toml
"weave-haystack>=2.0.0"        # W&B integration for Haystack
"pandas>=2.3.3"                # Data analysis
"numpy"                        # Statistical computations
```

### Environment Configuration

**Required Environment Variables**:
```bash
# API Keys
OPENAI_API_KEY="your_openai_api_key"
WANDB_API_KEY="your_wandb_api_key"

# Dual Elasticsearch Infrastructure
ELASTICSEARCH_SMALL_HOST="localhost:9200"  # Small embeddings instance (text-embedding-3-small)
ELASTICSEARCH_LARGE_HOST="localhost:9201"  # Large embeddings instance (text-embedding-3-large)
WANDB_PROJECT="rag_evaluation_ch6"         # W&B project name
```

**Dual Elasticsearch Setup**:
```bash
# Docker deployment (recommended) - starts both instances
docker-compose up -d

# Verify both instances are running
curl -s "localhost:9200/_cluster/health" | jq '.cluster_name'  # "es-small-cluster"
curl -s "localhost:9201/_cluster/health" | jq '.cluster_name'  # "es-large-cluster"

# Check instance specifications
curl -s "localhost:9200/_nodes/stats" | jq '.nodes[].jvm.mem.heap_max_in_bytes'  # 1GB heap
curl -s "localhost:9201/_nodes/stats" | jq '.nodes[].jvm.mem.heap_max_in_bytes'  # 4GB heap
```

**Python Environment**:
```bash
# Create virtual environment
python -m venv rag_env
source rag_env/bin/activate  # Linux/Mac
# rag_env\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Key Assumptions and Reproducibility

### Model and API Assumptions

1. **OpenAI API Access**: Requires valid OpenAI API key with sufficient credits for dual embedding model usage
2. **Dual Embedding Models**: 
   - `text-embedding-3-small` (1536-dim, $0.02/1M tokens) for cost-effective operations
   - `text-embedding-3-large` (3072-dim, $0.13/1M tokens) for maximum accuracy
3. **Dual Elasticsearch Infrastructure**: 
   - **Small Instance** (Port 9200): 1GB heap, optimized for small embeddings
   - **Large Instance** (Port 9201): 4GB heap, optimized for large embeddings  
4. **Compute Resources**: 
   - Minimum 8GB RAM for dual Elasticsearch instances
   - Additional 4GB recommended for embedding model processing
   - Docker with at least 6GB memory allocation

### Data Format Standards

**Evaluation Dataset Schema**:
```csv
question,ground_truth,contexts
"What is RAG?","RAG stands for...","[""Context 1"", ""Context 2""]"
```

**Dual Document Store Schema**:

**Small Embeddings Store** (Port 9200, Index: "small_embeddings"):
- **Content field**: Main document text
- **Embedding field**: Vector representations (1536-dim for text-embedding-3-small)
- **Metadata fields**: Source, title, chunk_id, etc.
- **Optimized for**: Speed and cost efficiency

**Large Embeddings Store** (Port 9201, Index: "large_embeddings"):
- **Content field**: Main document text  
- **Embedding field**: Vector representations (3072-dim for text-embedding-3-large)
- **Metadata fields**: Source, title, chunk_id, etc.
- **Optimized for**: Maximum accuracy and semantic understanding

### Reproducibility Measures

1. **Fixed Random Seeds**: Consistent results across runs
2. **Version Pinning**: Exact dependency versions in pyproject.toml  
3. **Configuration Logging**: All parameters tracked in W&B
4. **Docker Containers**: Consistent infrastructure setup
5. **Evaluation Dataset**: Fixed test sets for fair comparison

### Performance Baselines

**Expected Performance Ranges** (based on dual embedding architecture evaluation):

**Small Embeddings (text-embedding-3-small)**:
- **Naive RAG**: Faithfulness: 0.7-0.8, Context Recall: 0.6-0.7, Cost: $0.008-0.015/query
- **Hybrid RAG**: Faithfulness: 0.8-0.9, Context Recall: 0.7-0.85, Cost: $0.012-0.025/query

**Large Embeddings (text-embedding-3-large)**:  
- **Naive RAG**: Faithfulness: 0.75-0.85, Context Recall: 0.65-0.75, Cost: $0.025-0.040/query
- **Hybrid RAG**: Faithfulness: 0.85-0.95, Context Recall: 0.75-0.90, Cost: $0.030-0.055/query

**Performance vs Cost Trade-offs**:
- **Cost Efficiency Leader**: Small embeddings + Hybrid RAG (best performance per dollar)
- **Maximum Accuracy**: Large embeddings + Hybrid RAG (highest absolute performance) 
- **Budget Option**: Small embeddings + Naive RAG (lowest total cost)
- **Balanced Approach**: Small embeddings + Hybrid RAG (optimal cost-performance ratio)

---

## Complete Workflow Guide

### Phase 1: Dual Environment Setup and Data Preparation

```python
# 1. Load environment and initialize dual document stores
from dotenv import load_dotenv
load_dotenv()

# Small embeddings instance (fast, cost-effective)
small_document_store = ElasticsearchDocumentStore(
    hosts="http://localhost:9200",
    index="small_embeddings"
)

# Large embeddings instance (high accuracy)  
large_document_store = ElasticsearchDocumentStore(
    hosts="http://localhost:9201", 
    index="large_embeddings"
)

# 2. Create indexing pipelines for both embedding models
indexing_small_sc = IndexingPipelineSuperComponent(
    document_store=small_document_store,
    embedder_model="text-embedding-3-small"
)

indexing_large_sc = IndexingPipelineSuperComponent(
    document_store=large_document_store,
    embedder_model="text-embedding-3-large"
)

# Index documents to both stores for fair comparison
sources = [Path("documents/guide.pdf")]
urls = ["https://example.com/content"]

small_results = indexing_small_sc.run({"sources": sources, "urls": urls})
large_results = indexing_large_sc.run({"sources": sources, "urls": urls})
```

### Phase 2: Dual SuperComponent Creation and Configuration

```python
# 3. Create RAG SuperComponents for both embedding models

# Small embeddings RAG components (fast, cost-effective)
naive_rag_small_sc = NaiveRAGSuperComponent(
    document_store=small_document_store,
    embedder_model="text-embedding-3-small",
    llm_model="gpt-4o-mini",
    top_k=3
)

hybrid_rag_small_sc = HybridRAGSuperComponent(
    document_store=small_document_store,
    embedder_model="text-embedding-3-small", 
    llm_model="gpt-4o-mini",
    top_k=3,
    ranker_model="BAAI/bge-reranker-base"
)

# Large embeddings RAG components (high accuracy)
naive_rag_large_sc = NaiveRAGSuperComponent(
    document_store=large_document_store,
    embedder_model="text-embedding-3-large",
    llm_model="gpt-4o-mini",
    top_k=3
)

hybrid_rag_large_sc = HybridRAGSuperComponent(
    document_store=large_document_store,
    embedder_model="text-embedding-3-large",
    llm_model="gpt-4o-mini", 
    top_k=3,
    ranker_model="BAAI/bge-reranker-base"
)
```

### Phase 3: Dual Evaluation Pipeline Setup

```python
# 4. Create evaluation SuperComponents for both embedding models

# Small embeddings evaluation
naive_small_evaluation_sc = RAGEvaluationSuperComponent(
    rag_supercomponent=naive_rag_small_sc,
    system_name="Naive_RAG_Small_Embeddings",
    llm_model="gpt-4o-mini"
)

hybrid_small_evaluation_sc = RAGEvaluationSuperComponent(
    rag_supercomponent=hybrid_rag_small_sc,
    system_name="Hybrid_RAG_Small_Embeddings", 
    llm_model="gpt-4o-mini"
)

# Large embeddings evaluation
naive_large_evaluation_sc = RAGEvaluationSuperComponent(
    rag_supercomponent=naive_rag_large_sc,
    system_name="Naive_RAG_Large_Embeddings",
    llm_model="gpt-4o-mini"
)

hybrid_large_evaluation_sc = RAGEvaluationSuperComponent(
    rag_supercomponent=hybrid_rag_large_sc,
    system_name="Hybrid_RAG_Large_Embeddings",
    llm_model="gpt-4o-mini"
)
```

### Phase 4: Comprehensive Dual Evaluation

```python
# 5. Run evaluations on same dataset across all configurations
csv_file_path = "data_for_eval/synthetic_tests.csv"

# Small embeddings evaluation
naive_small_results = naive_small_evaluation_sc.run({"csv_source": csv_file_path})
hybrid_small_results = hybrid_small_evaluation_sc.run({"csv_source": csv_file_path})

# Large embeddings evaluation  
naive_large_results = naive_large_evaluation_sc.run({"csv_source": csv_file_path})
hybrid_large_results = hybrid_large_evaluation_sc.run({"csv_source": csv_file_path})
```

### Phase 5: Comprehensive Analytics and Experiment Tracking

```python
# 6. Initialize W&B tracking for dual embedding comparison
import wandb

wandb.init(project="rag_evaluation_ch6", name="dual_embedding_comparison")

# Create analytics instances for all configurations
naive_small_analytics = RAGAnalytics(naive_small_results, model_name="gpt-4o-mini", embedding_model="text-embedding-3-small")
hybrid_small_analytics = RAGAnalytics(hybrid_small_results, model_name="gpt-4o-mini", embedding_model="text-embedding-3-small")
naive_large_analytics = RAGAnalytics(naive_large_results, model_name="gpt-4o-mini", embedding_model="text-embedding-3-large") 
hybrid_large_analytics = RAGAnalytics(hybrid_large_results, model_name="gpt-4o-mini", embedding_model="text-embedding-3-large")

# Log comprehensive dual embedding comparison
wandb.log({
    # Small embeddings metrics
    "naive_small_faithfulness": naive_small_analytics.costs["avg_faithfulness"],
    "hybrid_small_faithfulness": hybrid_small_analytics.costs["avg_faithfulness"], 
    "naive_small_total_cost": naive_small_analytics.costs["total_cost"],
    "hybrid_small_total_cost": hybrid_small_analytics.costs["total_cost"],
    
    # Large embeddings metrics
    "naive_large_faithfulness": naive_large_analytics.costs["avg_faithfulness"],
    "hybrid_large_faithfulness": hybrid_large_analytics.costs["avg_faithfulness"],
    "naive_large_total_cost": naive_large_analytics.costs["total_cost"], 
    "hybrid_large_total_cost": hybrid_large_analytics.costs["total_cost"],
    
    # Cost efficiency analysis
    "small_vs_large_cost_ratio": naive_small_analytics.costs["total_cost"] / naive_large_analytics.costs["total_cost"],
    "performance_per_dollar_small": hybrid_small_analytics.costs["avg_faithfulness"] / hybrid_small_analytics.costs["total_cost"],
    "performance_per_dollar_large": hybrid_large_analytics.costs["avg_faithfulness"] / hybrid_large_analytics.costs["total_cost"]
})

# Generate comprehensive comparison reports
small_comparison_df = create_comparison_report(naive_small_results, hybrid_small_results)
large_comparison_df = create_comparison_report(naive_large_results, hybrid_large_results)
embedding_comparison_df = create_embedding_comparison_report(
    {"small": hybrid_small_results, "large": hybrid_large_results}
)

wandb.log({
    "small_embeddings_comparison": wandb.Table(dataframe=small_comparison_df),
    "large_embeddings_comparison": wandb.Table(dataframe=large_comparison_df), 
    "embedding_model_comparison": wandb.Table(dataframe=embedding_comparison_df)
})
```

### Phase 6: Advanced Analysis and Optimization

```python
# 7. Cross-architecture performance analysis
def analyze_architecture_performance():
    """
    Comprehensive analysis across dual embedding architectures
    """
    
    # Performance vs Cost Analysis
    configurations = {
        "naive_small": (naive_small_analytics, "Low cost, baseline performance"),
        "hybrid_small": (hybrid_small_analytics, "Balanced cost-performance"), 
        "naive_large": (naive_large_analytics, "High cost, improved baseline"),
        "hybrid_large": (hybrid_large_analytics, "Premium accuracy solution")
    }
    
    # Identify optimal configuration based on requirements
    for name, (analytics, description) in configurations.items():
        performance_metrics = analytics.get_performance_summary()
        cost_metrics = analytics.get_cost_breakdown()
        
        wandb.log({
            f"{name}_performance_score": performance_metrics["weighted_score"],
            f"{name}_cost_per_query": cost_metrics["cost_per_query"], 
            f"{name}_description": description
        })
    
    # Generate optimization recommendations
    recommendations = generate_optimization_recommendations(configurations)
    wandb.log({"optimization_recommendations": recommendations})

analyze_architecture_performance()

# 8. Infrastructure scaling analysis
scaling_analysis = analyze_elasticsearch_scaling({
    "small_instance": {"port": 9200, "heap": "1GB", "throughput": small_analytics.get_throughput()},
    "large_instance": {"port": 9201, "heap": "4GB", "throughput": large_analytics.get_throughput()}
})

wandb.log({"infrastructure_scaling": scaling_analysis})
```

---

## Learning Outcomes

By completing this chapter, you will have:

1. **Mastered SuperComponent Architecture**: Understanding how to abstract complex pipelines into reusable components
2. **Implemented Production RAG Systems**: Both naive and hybrid approaches with real performance characteristics
3. **Established Evaluation Workflows**: Systematic comparison frameworks using RAGAS metrics
4. **Built Analytics Infrastructure**: Cost tracking, performance monitoring, and experiment management
5. **Created Reproducible Experiments**: Standardized methodologies for RAG system comparison
6. **Gained Practical Experience**: Real-world patterns for scaling RAG applications

## Next Steps

- **Custom Component Development**: Create specialized components for your domain
- **Advanced Evaluation Metrics**: Implement custom RAGAS metrics or domain-specific evaluations
- **Production Deployment**: Scale SuperComponents to production environments
- **Hyperparameter Optimization**: Systematic tuning of retrieval and generation parameters
- **Multi-Modal RAG**: Extend patterns to handle images, audio, or structured data

---

This architecture provides a solid foundation for building, evaluating, and improving RAG systems at scale. The SuperComponent pattern ensures maintainability, the evaluation framework guarantees systematic comparison, and the analytics infrastructure enables data-driven optimization decisions.
