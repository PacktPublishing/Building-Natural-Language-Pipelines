# Description

Exercises for Chapter 8. "Hands-on projects"

## Projects

This chapter contains hands-on projects that progress from beginner to advanced complexity. Each project builds on concepts from the previous ones while introducing new techniques. The projects include complete notebooks with custom component definition, pipeline definition and pipeline serialization and are focused on three key areas: Named Entity Recognition, Text Classification and Multi-agentic systems that use Haystack pipelines as deployed endpoints through Hayhooks and define agentic architecture using LangGraph 1.0.

## Learning Path

**Recommended order:**
1. Start with **NER** to understand Haystack basics
2. Progress to **Text Classification** to learn API integration and evaluation
3. Advance to **Yelp Navigator** to master pipeline chaining and multi-agent systems

Each project includes detailed notebooks, documentation, and example outputs to guide your learning.


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
4. **(Recommended) Open this `ch8` folder in a new VS Code window.**
5. **Select the virtual environment as the Jupyter kernel:**
	- Open any notebook.
	- Click the kernel picker (top right) and select the `.venv` environment.

6. **Set up API keys:**

Create a `.env` file in the root directory with your API keys:
```sh
OPENAI_API_KEY=your_openai_key_here
RAPID_API_KEY=your_rapid_api_key_here
SEARCH_API_KEY=your_search_api_key_here
```

To obtain the API key:
- OpenAI API key: Sign up at [OpenAI's platform](https://platform.openai.com)
- Search API key: Sign ut at [Search API](https://www.searchapi.io/)
- Rapid API key: Sign up at [Rapid API Yelp Business Review API](https://rapidapi.com/beat-analytics-beat-analytics-default/api/yelp-business-reviews)

This notebook uses the Yelp Business Reviews API through RapidAPI:
- Sign up at: https://rapidapi.com/beat-analytics-beat-analytics-default/api/yelp-business-reviews
- Store your API key in a `.env` file as `RAPID_API_KEY`


---

### 1. Named Entity Recognition (NER) - **Beginner** 👶
📁 [named-entity-recognition/](./named-entity-recognition/)

Learn the fundamentals of building Haystack pipelines by extracting named entities (people, organizations, locations) from text.

**What you'll learn:**
- Building basic Haystack pipelines
- Using pre-trained NER models
- Creating custom components
- Processing web content

**Projects:**
- [Extracting entities from a dataset](./named-entity-recognition/ner-with-haystack-search-pipeline.ipynb) - Stand-alone component usage
- [Web search + NER pipeline with an Agent](./named-entity-recognition/ner-with-haystack-search-pipeline.ipynb) - Pipeline with custom components, supercomponent definition, and single-agent capabilities.

---

### 2. Text Classification & Sentiment Analysis - **Intermediate** 📊
📁 [text-classification/](./text-classification/)

Build on pipeline basics by implementing classification systems that categorize content and analyze sentiment without training data.

**What you'll learn:**
- Zero-shot classification techniques
- Integrating external APIs (Yelp)
- Evaluating model performance
- Building sentiment analysis pipelines

**Projects:**
- [Zero-shot text classification](./text-classification/text-classification.ipynb) - Evaluate classification on labeled datasets
- [Web-based news classification](./text-classification/classification-with-haystack-search-pipeline.ipynb) - Classify articles from web searches
- [Yelp review sentiment analysis](./text-classification/sentiment_analysis.ipynb) - Custom components for sentiment analysis
- [Mini challenge](./text-classification/haystack-agents-mini-project/) - Combine NER, text classification through your own custom components. Package, serialize and expose pipelines as REST endpoints. Add agentic capabilities with the Haystack API. **It is strongly recommended you complete this project before advancing to the final challenge**

---

### 3. Yelp Navigator - Multi-Agent System - **Advanced** 🚀
📁 [yelp-navigator/](./yelp-navigator/)

Master advanced techniques by building a complete multi-agent orchestration system that chains multiple pipelines and coordinates specialized agents.

**What you'll learn:**
- Chaining multiple Haystack pipelines
- Deploying pipelines with Hayhooks (REST APIs)
- Building multi-agent systems with LangGraph
- Implementing supervisor patterns
- Handling ambiguous user inputs
- Generating comprehensive reports from distributed data

**Guides:**
- [Pipeline Setup Guide](./yelp-navigator/yelp-navigator-hayhooks-guide.md) - Build and deploy with Hayhooks
- [Multi-Agent Guide](./yelp-navigator/LANGGRAPH_GUIDE.md) - Run the LangGraph supervisor system

**Projects:**

Please ensure to complete the Pipeline Setup Guide before you can execute the following notebooks: 

- [Pipeline chaining guide](./yelp-navigator/pipeline_chaining_guide.ipynb) - Connect multiple pipelines together
- [LangGraph multi-agent supervisor](./yelp-navigator/langgraph_multiagent_supervisor.ipynb) - Intelligent agent orchestration
- [4 modular pipelines](./yelp-navigator/pipelines/) - Business search, details, sentiment, and reporting


