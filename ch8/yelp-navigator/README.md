# Yelp Navigator - Multi-Agent System with Haystack Pipelines

This folder contains resources for building an advanced multi-agent orchestration system using LangGraph and Haystack pipelines. The system coordinates specialized agents to search for businesses, fetch details, analyze reviews, and generate comprehensive reports.

## Table of Contents

- [Main Objective](#main-objective)
- [Use Cases](#use-cases)
- [Getting Started](#getting-started)
- [Architecture Overview](#architecture-overview)
- [Contents](#contents)
- [Key Features](#key-features)
- [Support](#support)

---

## Main Objective

The primary goal of these resources is to teach you how to:

1. **Build Chained Haystack Pipelines**: Create modular pipelines that pass data between each other for complex workflows
2. **Orchestrate Multi-Agent Systems**: Use LangGraph to coordinate specialized agents with conditional routing
3. **Implement Quality Control Patterns**: Build supervisor approval agents that review outputs and request revisions
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

## Getting Started

### Prerequisites

Complete the [setup instructions](../README.md#setup-instructions)

### Quick Start

**Option 1: Pipeline Chaining (Intermediate)**
1. Deploy pipelines: `uv run sh build_all_pipelines.sh && uv run hayhooks run --pipelines-dir pipelines`
2. Open: [pipeline_chaining_guide.ipynb](./pipeline_chaining_guide.ipynb)
3. Learn to chain Haystack pipeline API calls

**Option 2: Multi-Agent System (Advanced)**
1. Deploy pipelines (same as above)
2. Open: [langgraph_multiagent_supervisor.ipynb](./langgraph_multiagent_supervisor.ipynb)
3. Run the full multi-agent orchestration system

📖 **Detailed guides**: See [Contents](#contents) section below

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
Clarification Agent
    ↓
Search Agent (Pipeline 1) - always runs
    ↓
    ├─→ Details Agent (Pipeline 2) - conditional: "detailed" or "reviews"
    │       ↓
    └─→ Sentiment Agent (Pipeline 3) - conditional: "reviews" only
            ↓
        Summary Agent
            ↓
    Supervisor Approval - reviews quality, can request revisions
            ↓
      Final Report to User
```

---

## Contents

### 📚 Guides

| Resource | Description |
|---|---|
| [**Pipeline Setup Guide**](./yelp-navigator-hayhooks-guide.md) | Complete setup for building and deploying Haystack pipelines with Hayhooks |
| [**LangGraph Multi-Agent Guide**](./langgraph-yelp-multi-agent.md) | Step-by-step guide for running the multi-agent supervisor system |
| [**API Documentation**](./Hayhooks%20-%20Swagger%20UI.pdf) | Swagger UI docs for deployed Haystack pipeline endpoints |
| [**Troubleshooting**](./TROUBLESHOOTING.md) | Common issues and solutions for API keys and connectivity |

### 📓 Notebooks

| Notebook | Level | Description |
|---|---|---|
| [**pipeline_chaining_guide.ipynb**](./pipeline_chaining_guide.ipynb) | Intermediate | Tutorial on chaining deployed Haystack pipelines with POST calls |
| [**langgraph_multiagent_supervisor.ipynb**](./langgraph_multiagent_supervisor.ipynb) | Advanced | Multi-agent system with supervisor pattern using deployed pipelines |

### 🔧 Pipeline Modules

| Pipeline | Purpose |
|---|---|
| [**business_search/**](./pipelines/business_search/) | Business search with NER entity extraction |
| [**business_details/**](./pipelines/business_details/) | Fetch and process business website content |
| [**business_sentiment/**](./pipelines/business_sentiment/) | Review fetching and sentiment analysis |
| [**business_summary_review/**](./pipelines/business_summary_review/) | Generate comprehensive business reports |

---

## Key Features

- **Modular Pipeline Design**: Each pipeline is independent and reusable
- **REST API Endpoints**: Pipelines exposed via Hayhooks for easy integration
- **Conditional Agent Routing**: Agents activate based on detail level requirements (general/detailed/reviews)
- **Quality Control Loop**: Supervisor approval reviews summaries and can request revisions (max 2 attempts)
- **Fallback Mechanisms**: Handles ambiguous queries and prevents infinite loops
- **Flexible Report Generation**: Adapts output depth based on available data

---

## Support

For issues or questions:
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common problems
- Review component implementations in `pipelines/*/components.py` files
- Verify pipeline connections in `pipelines/*/build_pipeline.py` files
