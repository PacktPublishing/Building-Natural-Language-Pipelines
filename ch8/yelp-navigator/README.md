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

### 🤖 LangGraph Helpers (`langgraph_helpers/`)

Modular components for building the multi-agent system:

**`agents.py`** - Core agent implementations
- `clarification_agent()` - Extracts query, location, and detail level from user input
  - Auto-defaults after 2 attempts to prevent infinite loops
  - Supports three detail levels: `general`, `detailed`, `reviews`
- `supervisor_approval_agent()` - Reviews summary quality and requests revisions
  - Max 2 approval attempts to prevent infinite revision loops
  - Can request re-running specific agents (search, details, sentiment, summary)

**`nodes.py`** - Agent node wrappers for LangGraph integration
- `search_agent_node()` - Wraps the search tool, routes to details or summary based on detail level
- `details_agent_node()` - Fetches website content, conditionally routes to sentiment
- `sentiment_agent_node()` - Analyzes reviews, always routes to summary
- `summary_agent_node()` - Synthesizes all agent outputs into user-friendly response

**`tools.py`** - LangChain tool wrappers for Hayhooks pipelines
- `search_businesses()` - POST to `/business_search/run` endpoint
- `get_business_details()` - POST to `/business_details/run` endpoint
- `analyze_reviews_sentiment()` - POST to `/business_sentiment/run` endpoint
- `set_base_url()` - Configure Hayhooks server URL

**Key Design Patterns:**
- **Conditional Routing**: Agents set `next_agent` in state to control workflow
- **Shared State**: `AgentState` TypedDict maintains conversation and results
- **Tool Integration**: Each agent wraps external tools and updates shared state
- **Quality Control**: Supervisor pattern with revision feedback loop

---

## System Architecture

**Pipeline Chain**: Search → Details → Sentiment → Report  
**Multi-Agent Flow**: Clarification → Search → Conditional(Details + Sentiment) → Summary → Supervisor Approval → User
