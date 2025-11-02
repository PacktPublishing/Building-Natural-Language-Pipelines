# Chapter 5: Haystack Pipeline Development with Custom Components

This repository contains exercises and interactive notebooks for Chapter 5, focusing on developing custom components for Haystack pipelines and advanced pipeline architectures.

## Setup Instructions

1. **Install [uv](https://github.com/astral-sh/uv):**
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
4. **(Recommended) Open this `ch5` folder in a new VS Code window.**
5. **Select the virtual environment as the Jupyter kernel:**
	- Open any notebook.
	- Click the kernel picker (top right) and select the `.venv` environment.

6. **Set up API keys:**

Create a `.env` file in the root directory with your API keys:
```sh
OPENAI_API_KEY=your_openai_key_here
```

To obtain the API key:
- OpenAI API key: Sign up at [OpenAI's platform](https://platform.openai.com)

---

## Contents

| Notebook | Link | Description |
|---|---|---|
| Introduction to Custom Components | [prefixed_custom-component.ipynb](./jupyter-notebooks/prefixed_custom-component.ipynb) | Learn the fundamentals of creating custom Haystack components |
| The Warmup method | [warmup_component.ipynb](./jupyter-notebooks/warmup_component.ipynb) | Learn the fundamentals of creating custom Haystack components |
| PDF Knowledge Graph Pipeline | [pdf_knowledge_graph_pipeline.ipynb](./jupyter-notebooks/pdf_knowledge_graph_pipeline.ipynb) | PDF processing pipeline for knowledge graphs and synthetic test generation |
| Web Content Knowledge Graph Pipeline | [web_knowledge_graph_pipeline.ipynb](./jupyter-notebooks/web_knowledge_graph_pipeline.ipynb) | Web content processing pipeline for knowledge graphs and synthetic test generation |
| Advanced Branching Pipeline | [advanced_branching_pipeline.ipynb](./jupyter-notebooks/advanced_branching_pipeline.ipynb) | Multi-source branching pipeline with FileTypeRouter and DocumentJoiner |

### Component Scripts and Tests

| Component | Link | Description |
|---|---|---|
| Knowledge Graph Components | [knowledge_graph_component.py](./jupyter-notebooks/scripts/knowledge_graph_component.py) | Production-ready knowledge graph components |
| Synthetic Test Components | [synthetic_test_components.py](./jupyter-notebooks/scripts/synthetic_test_components.py) | Components for generating synthetic test datasets |

Images for component diagrams and pipeline visualizations are in `jupyter-notebooks/images/`.

Testing scripts and execution can be found [in this folder](./tests/README.md)

---

## Pipeline Progression

The knowledge graph and synthetic data generation notebooks are organized in increasing complexity:

### 1. PDF Knowledge Graph Pipeline
- **Focus**: Single input type (PDF files)
- **Components**: PyPDFToDocument → DocumentCleaner → DocumentSplitter → KnowledgeGraphGenerator → SyntheticTestGenerator
- **Best for**: Learning the basics of knowledge graph generation from documents
- **Output**: Synthetic test dataset from PDF content

### 2. Web Content Knowledge Graph Pipeline  
- **Focus**: Single input type (web URLs)
- **Components**: LinkContentFetcher → HTMLToDocument → DocumentCleaner → DocumentSplitter → KnowledgeGraphGenerator → SyntheticTestGenerator
- **Best for**: Understanding web content processing and comparing with PDF results
- **Output**: Synthetic test dataset from web content

### 3. Advanced Branching Pipeline
- **Focus**: Multiple input types (PDFs + Web + Text files)
- **Components**: FileTypeRouter + DocumentJoiner for intelligent multi-source processing
- **Best for**: Production-ready pipelines that need to handle diverse document collections
- **Output**: Unified synthetic test dataset from multiple sources

---

## Chapter Topics Covered

1. **How to define Haystack custom components**

2. **Integrating your custom component into a pipeline**

3. **Advanced Custom Component Feature implementation**
   - Knowledge graph generation components
   - Synthetic test data generation
   - Multi-format document processing
   - Branching pipeline architectures with FileTypeRouter and DocumentJoiner

4. **Testing and Debugging Custom Components**
