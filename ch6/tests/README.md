# Custom Component Tests

This directory contains comprehensive tests for all custom Haystack components developed in Chapter 5.

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

## Running Tests

### Option 1: Run All Tests (Recommended)
```bash
# From project root (ch5/)
uv run tests/run_tests.py

# Or from tests directory
cd tests
uv run run_tests.py
```

### Option 2: Run Individual Test Files
```bash
# From project root (ch5/)
uv run tests/test_synthetic_test_components.py
uv run tests/test_knowledge_graph_component.py

# Or from tests directory
cd tests
uv run test_synthetic_test_components.py
uv run test_knowledge_graph_component.py
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


## Mocking Strategy

Tests use comprehensive mocking to:
- **Avoid external API calls** (OpenAI, model downloads)
- **Simulate realistic component behavior** without dependencies
- **Test error conditions** that are difficult to reproduce naturally
- **Ensure fast test execution** without network dependencies


