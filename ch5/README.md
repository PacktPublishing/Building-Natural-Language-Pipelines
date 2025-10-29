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
| Error Handling | [custom-component-error-handling.ipynb](./jupyter-notebooks/custom-component-robustness/custom-component-error-handling.ipynb) | Build robust components with comprehensive error handling |
| Logging Implementation | [custom-component-logging.ipynb](./jupyter-notebooks/custom-component-robustness/custom-component-logging.ipynb) | Add proper logging to custom components for debugging |
| Global State Management | [custom-component-logging-threading.ipynb](./jupyter-notebooks/custom-component-robustness/custom-component-logging-threading.ipynb) | Implement custom components with threading and global state |
| Scalability Considerations | [custom-component-scalability.ipynb](./jupyter-notebooks/custom-component-robustness/custom-component-scalability.ipynb) | Design components that scale efficiently in production |
| Knowledge Graph & Synthetic Data | [knowledgegraph_sdg_pipelines.ipynb](./jupyter-notebooks/knowledgegraph_sdg_pipelines.ipynb) | Advanced pipeline for knowledge graphs and synthetic test generation |

### Component Scripts and Tests

| Component | Link | Description |
|---|---|---|
| Knowledge Graph Components | [knowledge_graph_component.py](./jupyter-notebooks/scripts/knowledge_graph_component.py) | Production-ready knowledge graph components |
| Synthetic Test Components | [synthetic_test_components.py](./jupyter-notebooks/scripts/synthetic_test_components.py) | Components for generating synthetic test datasets |

Images for component diagrams and pipeline visualizations are in `jupyter-notebooks/images/`.



---

## Chapter Topics Covered

1. **How to define Haystack custom components**

2. **Integrating your custom component into a pipeline**

3. **Advanced Custom Component Feature implementation**
   - Knowledge graph generation components
   - Synthetic test data generation
   - Multi-format document processing

4. **Testing and Debugging Custom Components**
