# Yelp Navigator - Multi-Agent System with Haystack Pipelines

This folder contains resources for building an advanced multi-agent orchestration system using LangGraph and Haystack pipelines. The system coordinates specialized agents to search for businesses, fetch details, analyze reviews, and generate comprehensive reports.

## Main Objective

The primary goal of these resources is to teach you how to:

1. **Build Chained Haystack Pipelines**: Create modular pipelines that pass data between each other for complex workflows
2. **Orchestrate Multi-Agent Systems**: Use LangGraph to coordinate specialized agents that delegate tasks intelligently
3. **Implement Agent Supervision Patterns**: Build supervisor agents that route work to specialized agents based on requirements
4. **Integrate External APIs**: Connect multiple third-party services (Yelp, web scraping, NER, sentiment analysis)
5. **Deploy with Hayhooks**: Expose Haystack pipelines as REST API endpoints for agent consumption
6. **Handle Ambiguous Inputs**: Implement clarification mechanisms and fallback behaviors for robust agent interactions

## Use Cases

These multi-agent pipeline systems are valuable for:
- **Business Intelligence**: Automated research and analysis of businesses and competitors
- **Market Research**: Gather and synthesize information from multiple sources
- **Customer Experience Analysis**: Analyze reviews and sentiment across multiple businesses
- **Recommendation Systems**: Generate personalized recommendations with supporting evidence
- **Automated Report Generation**: Create comprehensive reports from distributed data sources
- **Agent-Based Workflows**: Coordinate complex tasks that require multiple specialized capabilities

---

## Contents

### Guides

| Guide | Link | Description |
|---|---|---|
| **Pipeline Setup Guide** | [yelp-navigator-hayhooks-guide.md](./yelp-navigator-hayhooks-guide.md) | Complete setup instructions for building and deploying Haystack pipelines with Hayhooks |
| **API Swagger Documentation** | [Deployed Endpoint Documentation](./Hayhooks%20-%20Swagger%20UI.pdf) | Check the docs of our deployed Haystack pipelines through Hayhooks
| **LangGraph Multi-Agent Guide** | [langgraph-yelp-multi-agent.md](./langgraph-yelp-multi-agent.md) | Step-by-step guide for running the multi-agent supervisor system |
| **Troubleshooting** | [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | Common issues and solutions for API keys and pipeline connectivity |

### Notebooks

| Notebook | Link | Description |
|---|---|---|
| **Pipeline Chaining** | [pipeline_chaining_guide.ipynb](./pipeline_chaining_guide.ipynb) | Tutorial on making POST calls to deployed Haystack pipelines together for complex workflows |
| **LangGraph Supervisor** | [langgraph_multiagent_supervisor.ipynb](./langgraph_multiagent_supervisor.ipynb) | Multi-agent system with supervisor pattern for intelligent task delegation that uses deployed Haystack pipelines |


### Pipeline Modules

| Pipeline | Directory | Purpose |
|---|---|---|
| **Pipeline 1** | [pipelines/business_search/](./pipelines/business_search/) | Business search with NER entity extraction |
| **Pipeline 2** | [pipelines/business_details/](./pipelines/business_details/) | Fetch and process business website content |
| **Pipeline 3** | [pipelines/business_sentiment/](./pipelines/business_sentiment/) | Review fetching and sentiment analysis |
| **Pipeline 4** | [pipelines/business_summary_review/](./pipelines/business_summary_review/) | Generate comprehensive business reports |

---

## Architecture Overview

### Haystack Pipeline Chain
```
Pipeline 1: Business Search (NER)
    ↓
    ├──→ Pipeline 2: Website Details
    │        ↓
    └──→ Pipeline 3: Review Sentiment
             ↓
    ┌────────┴────────┐
    ↓                 ↓
Pipeline 4: Report Generator
```

### LangGraph Multi-Agent System
```
User Query
    ↓
Clarification Agent → Supervisor Agent
                           ↓
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                   ↓
   Search Agent      Details Agent     Sentiment Agent
   (Pipeline 1)      (Pipeline 2)      (Pipeline 3)
        │                  │                   │
        └──────────────────┼───────────────────┘
                           ↓
                    Summary Agent
                           ↓
                  Final Report to User
```

---

## Getting Started

### Quick Start (3 Steps)

1. **Setup environment**:
```bash
uv sync
source .venv/bin/activate
```

2. **Configure API keys** - Add to `.env` file:
   ```bash
   OPENAI_API_KEY=your_key_here
   RAPID_API_KEY=your_key_here
   ```


3. **Set up pipelines** - Follow [yelp-navigator-hayhooks-guide.md](./yelp-navigator-hayhooks-guide.md)
   ```bash
   sh build_all_pipelines.sh
   uv run hayhooks run --pipelines-dir pipelines
   ```

4. **Run the multi-agent system** - Follow [LANGGRAPH_GUIDE.md](./LANGGRAPH_GUIDE.md)
   ```bash
   jupyter notebook langgraph_multiagent_supervisor.ipynb
   ```

---

## Prerequisites

- Python 3.9+
- OpenAI API key (for LLM operations)
- RapidAPI key with Yelp Business Reviews subscription
- LangGraph and LangChain packages

---

## Key Features

- **Modular Pipeline Design**: Each pipeline is independent and reusable
- **REST API Endpoints**: Pipelines exposed via Hayhooks for easy integration
- **Intelligent Agent Routing**: Supervisor pattern dynamically activates agents based on requirements
- **Fallback Mechanisms**: Handles ambiguous queries and prevents infinite loops
- **Flexible Report Generation**: Adapts output depth based on available data
- **Production-Ready**: Includes error handling, logging, and configuration management

---

## Learn More

- Start with the **Pipeline Setup Guide** to build and deploy the Haystack pipelines
- Then explore the **LangGraph Multi-Agent Guide** to see agent orchestration in action
- Check **Pipeline Chaining Guide** notebook for in-depth pipeline integration examples

---

## Support

For issues or questions:
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common problems
- Review component implementations in `pipelines/*/components.py` files
- Verify pipeline connections in `pipelines/*/build_pipeline.py` files
