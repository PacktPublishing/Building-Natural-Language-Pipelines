# Custom Component Tests

This directory contains comprehensive tests for all custom Haystack components developed in Chapter 6.

## Test Files Overview

### `test_synthetic_test_components.py`
Tests for components in `synthetic_test_components.py`:
- **SyntheticTestGenerator**: Tests initialization, document handling, and test generation
- **TestDatasetSaver**: Tests CSV/JSON saving functionality and error handling  
- **DocumentToLangChainConverter**: Tests document format conversion between Haystack and LangChain

### `test_knowledge_graph_component.py`
Tests for components in `knowledge_graph_component.py`:
- **KnowledgeGraphGenerator**: Tests graph creation, transform application, and document processing
- **KnowledgeGraphSaver**: Tests graph serialization and file operations
- **Integration tests**: Tests component interaction and pipeline workflows

### `test_warmup_components.py`
Tests for warmup components from `warmup_component.ipynb`:
- **LocalEmbedderText**: Tests text embedding with warm-up patterns
- **LocalEmbedderDocs**: Tests document embedding with proper initialization
- **WarmUp patterns**: Tests idempotency, error handling, and best practices

### `test_rag_supercomponents.py` ⭐ **New**
Tests for RAG SuperComponents in `rag/` directory:
- **IndexingPipelineSuperComponent**: Tests pipeline initialization, component connections, multi-format document processing (PDF, HTML, text), and input/output mappings
- **NaiveRAGSuperComponent**: Tests baseline RAG implementation, query processing, response generation, and error handling
- **HybridRAGSuperComponent**: Tests dual retrieval (dense + sparse), document joining, re-ranking, pipeline connections, and configuration options

### `test_ragas_evaluation_components.py` ⭐ **New**
Tests for RAGAS evaluation framework in `ragas_evaluation/`:
- **CSVReaderComponent**: Tests CSV loading, file validation, and error handling for evaluation datasets
- **RAGDataAugmenterComponent**: Tests RAG SuperComponent integration, batch processing, and data augmentation workflows
- **RagasEvaluationComponent**: Tests RAGAS metrics calculation, LLM wrapper initialization, and evaluation dataset processing
- **RAGEvaluationSuperComponent**: Tests complete evaluation pipeline, component connections, and systematic comparison workflows
- **Comparison Utilities**: Tests comparison report generation and statistical analysis functions

### `test_rag_analytics.py` ⭐ **New** 
Tests for cost tracking and analytics in `wandb_experiments/`:
- **RAGAnalytics**: Tests cost calculations, token counting, pricing model support, performance metrics aggregation
- **Token Usage**: Tests tiktoken integration, input/output token calculation, and embedding token estimation
- **Cost Analysis**: Tests OpenAI pricing integration, cost per query calculation, and embedding cost analysis
- **W&B Integration**: Tests Weights & Biases logging, experiment tracking, and dashboard data preparation
- **Performance Metrics**: Tests RAGAS metrics aggregation, statistical summary generation, and comparison reporting

## Running Tests

### Option 1: Run All Tests (Recommended)
```bash
# From project root (ch6/)
python tests/run_tests.py

# Or from tests directory
cd tests
python run_tests.py
```

### Option 2: Run Individual Test Files
```bash
# From project root (ch6/)
python tests/test_synthetic_test_components.py
python tests/test_knowledge_graph_component.py
python tests/test_warmup_components.py
python tests/test_rag_supercomponents.py                    # New RAG SuperComponent tests
python tests/test_ragas_evaluation_components.py           # New evaluation framework tests
python tests/test_rag_analytics.py                         # New analytics and cost tracking tests

# Or from tests directory
cd tests
python test_synthetic_test_components.py
python test_knowledge_graph_component.py
python test_warmup_components.py
python test_rag_supercomponents.py
python test_ragas_evaluation_components.py
python test_rag_analytics.py
```

## Test Coverage

### SyntheticTestGenerator Component
- ✅ Component initialization with various parameters
- ✅ Empty document list handling
- ✅ Mock-based test generation validation

### TestDatasetSaver Component
- ✅ CSV format saving and loading
- ✅ JSON format support
- ✅ File path and directory creation

### DocumentToLangChainConverter Component
- ✅ Successful document conversion
- ✅ Empty document list handling
- ✅ Metadata preservation and None handling

### KnowledgeGraphGenerator Component
- ✅ Component initialization and configuration
- ✅ Empty document handling
- ✅ Knowledge graph creation with transforms

### KnowledgeGraphSaver Component
- ✅ Initialization with custom paths
- ✅ Successful graph serialization
- ✅ Error handling for failed saves

### LocalEmbedder Components
- ✅ Warm-up method implementation and idempotency
- ✅ Error handling before warm-up
- ✅ Text/document processing after initialization

## New RAG Architecture Test Coverage ⭐

### RAG SuperComponents
- ✅ **IndexingPipelineSuperComponent**: Pipeline initialization, multi-format processing, component connections
- ✅ **NaiveRAGSuperComponent**: Query processing, response generation, error handling
- ✅ **HybridRAGSuperComponent**: Dual retrieval, re-ranking, pipeline connections, configuration validation

### RAGAS Evaluation Framework
- ✅ **CSVReaderComponent**: File validation, empty file handling, column schema verification
- ✅ **RAGDataAugmenterComponent**: RAG integration, batch processing, data augmentation workflows
- ✅ **RagasEvaluationComponent**: Metrics calculation, LLM wrapper initialization, evaluation processing
- ✅ **RAGEvaluationSuperComponent**: Complete pipeline testing, component connections, input/output mappings

### Analytics and Cost Tracking
- ✅ **RAGAnalytics**: Token counting, cost calculations, performance metrics, W&B integration
- ✅ **Pricing Models**: Multiple OpenAI model support, embedding cost calculation, cost per query analysis
- ✅ **Performance Analysis**: Metrics aggregation, comparison reporting, statistical analysis

## Test Requirements

### Environment Variables (Mocked in Tests)
```bash
export OPENAI_API_KEY="test-key"  # Any value works for testing
export WANDB_API_KEY="test-key"   # Any value works for testing
```

### Dependencies
All testing dependencies are included in `pyproject.toml`:
- `pytest>=8.4.2` - Testing framework
- `pandas>=2.3.3` - Data analysis and manipulation  
- `unittest.mock` - Mocking (built into Python)
- `tempfile` - Temporary file handling (built into Python)

## Mocking Strategy

Tests use comprehensive mocking to:
- **Avoid external API calls** (OpenAI, model downloads, Elasticsearch, W&B)
- **Simulate realistic component behavior** without dependencies
- **Test error conditions** that are difficult to reproduce naturally
- **Ensure fast test execution** without network dependencies
- **Validate pipeline connections** and data flow between components
- **Test cost calculations** with predictable token counts and pricing


