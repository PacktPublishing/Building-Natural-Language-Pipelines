# Yelp Navigator - Multi-Agent System with Haystack Pipelines

Build an advanced multi-agent orchestration system using LangGraph and Haystack pipelines. The system coordinates specialized agents to search for businesses, fetch details, analyze reviews, and generate comprehensive reports.

## Quick Start

**Prerequisites**: Complete the [setup instructions](../README.md#setup-instructions)

### Choose Your Path

**🚀 Option 1: Pipeline Chaining** (Intermediate)
1. Deploy pipelines: `uv run sh build_all_pipelines.sh && sh start_hayhooks.sh`
2. Open: [pipeline_chaining_guide.ipynb](./pipeline_chaining_guide.ipynb)
3. Learn to chain Haystack pipeline API calls

**🤖 Option 2: Multi-Agent System with LangGraph** (Advanced)
1. Deploy pipelines (same command as above)
2. Open: [langgraph_multiagent_supervisor.ipynb](./langgraph_multiagent_supervisor.ipynb)
3. Run the full multi-agent orchestration system with LangGraph

Case studies - can we enable the same amount of fluid decision making with Haystack?

**🔄 Case study 1: Using the `Agent` class ** 
1. Deploy pipelines (same command as above)
2. Open: [haystack_agent_with_tools.ipynb](./haystack_agent_with_tools.ipynb)
3. Run the same multi-agent pattern implemented natively in Haystack


**🔄 Case study 2: Using built-in primitives ** 
1. Deploy pipelines (same command as above)
2. Open: [haystack_looping_supervisor.ipynb](./haystack_looping_supervisor.ipynb)
3. Run the same multi-agent pattern implemented natively in Haystack



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
- [langgraph_multiagent_supervisor.ipynb](./langgraph_multiagent_supervisor.ipynb) - Multi-agent system with supervisor pattern (LangGraph)
- [haystack_multiagent_supervisor.ipynb](./haystack_multiagent_supervisor.ipynb) - Multi-agent system with supervisor pattern (Haystack native)

### 📚 Documentation
- [Pipeline Setup Guide](./docs/yelp-navigator-hayhooks-guide.md) - Deploy pipelines with Hayhooks
- [Multi-Agent Guide](./docs/langgraph-yelp-multi-agent.md) - Run the multi-agent supervisor system
- [Troubleshooting](./docs/TROUBLESHOOTING.md) - Common issues and solutions

### 🔧 Pipelines
- `business_search/` - Business search with NER entity extraction
- `business_details/` - Website content fetching and processing
- `business_sentiment/` - Review fetching and sentiment analysis

### 🤖 Agent Helpers 

**LangGraph Implementation:**
- [`langgraph_helpers/`](./langgraph_helpers/)
  - **`nodes.py`** - Search, details, sentiment, summary and approval nodes
  - **`tools.py`** - Wrappers for calling Hayhooks pipeline endpoints

**Haystack Implementation:**
- [`haystack_helpers/`](./haystack_helpers/)
  - **`components.py`** - Custom Haystack components (ClarificationComponent, SearchComponent, etc.)
  - **`state.py`** - Shared state management for multi-agent coordination

---

## System Architecture

### Pipeline Chain (Simple)
Search → Details → Sentiment → Report

### Multi-Agent Flow (Advanced)
Clarification → Search → Conditional(Details + Sentiment) → Summary → Supervisor Approval → User

### Implementation Approaches

**LangGraph Implementation** ([langgraph_multiagent_supervisor.ipynb](./langgraph_multiagent_supervisor.ipynb))
- Uses `StateGraph` for workflow orchestration
- Inherits from `MessagesState` for automatic message handling
- Conditional routing with `add_conditional_edges`
- Graph-based visualization with Mermaid

**Haystack Implementation** ([haystack_multiagent_supervisor.ipynb](./haystack_multiagent_supervisor.ipynb))
- Uses Haystack `Pipeline` with custom components
- State management via `StateMultiplexer` components
- Feedback loops via component output connections
- Native Haystack pipeline visualization

Both implementations follow the same multi-agent supervisor pattern with identical functionality, demonstrating how the same architectural pattern can be expressed in different frameworks.
