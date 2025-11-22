# Yelp Navigator - Multi-Agent System with Haystack Pipelines

Build an advanced multi-agent orchestration system using LangGraph and Haystack pipelines. The system coordinates specialized agents to search for businesses, fetch details, analyze reviews, and generate comprehensive reports.

## Quick Start

**Prerequisites**: Complete the [setup instructions](../README.md#setup-instructions)

### Choose Your Path

**🚀 Option 1: Pipeline Chaining** (Intermediate)
1. Deploy pipelines: `uv run sh build_all_pipelines.sh && sh start_hayhooks.sh`
2. Open: [pipeline_chaining_guide.ipynb](./pipeline_chaining_guide.ipynb)
3. Learn to chain Haystack pipeline API calls

**🤖 Option 2: Multi-Agent System** (Advanced)
1. Deploy pipelines (same command as above)
2. Open: [langgraph_multiagent_supervisor.ipynb](./langgraph_multiagent_supervisor.ipynb)
3. Run the full multi-agent orchestration system

---

## What You'll Learn

- Build chained Haystack pipelines that pass data between each other
- Orchestrate multi-agent systems with LangGraph and conditional routing
- Implement supervisor approval patterns for quality control
- Integrate external APIs (Yelp, web scraping, NER, sentiment analysis)
- Deploy pipelines as REST APIs with Hayhooks
- Handle ambiguous inputs with clarification mechanisms

---

## Resources

### 📓 Notebooks
- [pipeline_chaining_guide.ipynb](./pipeline_chaining_guide.ipynb) - Chain Haystack pipelines via REST API calls
- [langgraph_multiagent_supervisor.ipynb](./langgraph_multiagent_supervisor.ipynb) - Multi-agent system with supervisor pattern

### 📚 Documentation
- [Pipeline Setup Guide](./docs/yelp-navigator-hayhooks-guide.md) - Deploy pipelines with Hayhooks
- [Multi-Agent Guide](./docs/langgraph-yelp-multi-agent.md) - Run the multi-agent supervisor system
- [Troubleshooting](./docs/TROUBLESHOOTING.md) - Common issues and solutions

### 🔧 Pipelines
- `business_search/` - Business search with NER entity extraction
- `business_details/` - Website content fetching and processing
- `business_sentiment/` - Review fetching and sentiment analysis

### 🤖 LangGraph Helpers 

- [`langgraph_helpers/`](./langgraph_helpers/)

Modular components for the multi-agent system:

- **`agents.py`** - Clarification and supervisor agents
- **`nodes.py`** - Search, details, sentiment, and summary agent nodes
- **`tools.py`** - Wrappers for calling Hayhooks pipeline endpoints

---

## System Architecture

**Pipeline Chain**: Search → Details → Sentiment → Report  
**Multi-Agent Flow**: Clarification → Search → Conditional(Details + Sentiment) → Summary → Supervisor Approval → User
