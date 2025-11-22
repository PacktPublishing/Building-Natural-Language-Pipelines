
# Chapter 3: Introduction to Haystack by deepset

This repository contains exercises and interactive notebooks for Chapter 3, introducing Haystack's NLP pipeline and LLM orchestration framework.

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
4. **(Recommended) Open this `ch3` folder in a new VS Code window.**
5. **Select the virtual environment as the Jupyter kernel:**
	- Open any notebook.
	- Click the kernel picker (top right) and select the `.venv` environment.

6. **Create an .env file with your openai key**

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

| Notebook | Link | Description |
|---|---|---|
| Components | [components.ipynb](./jupyter-notebooks/components.ipynb) | Explore Haystack's core components for document cleaning, splitting, prompt building, and LLM generation. |
| Your First Pipeline | [your-first-pipeline.ipynb](./jupyter-notebooks/your-first-pipeline.ipynb) | Step-by-step guide to building and running a simple Haystack pipeline. |
| Your First Custom Component | [your-first-custom-component.ipynb](./jupyter-notebooks/your-first-custom-component.ipynb) | Learn how to design, implement, and use a custom Haystack component. |
| Supercomponents | [supercomponents.ipynb](./jupyter-notebooks/supercomponents.ipynb) | Create and use supercomponents to encapsulate reusable pipelines. |

Images for pipeline visualizations are in `jupyter-notebooks/images/`.

---

## Chapter topics covered

1. An overview of deepset
2. About Haystack’s NLP pipeline and LLM orchestration framework
3. Haystack key building blocks: components and pipelines
4. Key features and advantages
5. Use cases and applications
6. Architecture of Haystack
7. Incorporating Haystack into your workflow
