# LangGraph Multi-Agent Supervisor Guide

## Overview

This guide walks you through running the **LangGraph Multi-Agent Supervisor** system - an intelligent orchestration layer that coordinates multiple specialized agents to search for businesses on Yelp and generate comprehensive reports.

### What Does This Application Do?

The multi-agent system automates the process of finding and analyzing businesses:

1. **Understands your request** - Clarifies what you're looking for, where, and how much detail you need
2. **Delegates tasks** - A supervisor agent coordinates specialized worker agents
3. **Searches intelligently** - Finds relevant businesses using natural language queries
4. **Gathers details** - Optionally fetches website information and customer reviews
5. **Synthesizes results** - Creates a human-readable summary with recommendations

### Real-World Example

**You ask:** "I'm looking for good Mexican restaurants in Austin, Texas. I want to see customer reviews."

**The system:**
- **Clarification Agent** extracts: query="Mexican restaurants", location="Austin, Texas", detail_level="reviews"
- **Supervisor** decides to activate: Search Agent → Details Agent → Sentiment Agent
- **Search Agent** finds 10+ restaurants with ratings and locations
- **Details Agent** fetches website content for each restaurant
- **Sentiment Agent** analyzes customer reviews and identifies positive/negative themes
- **Summary Agent** generates a comprehensive report with top recommendations

## Architecture

![Multi-Agent Architecture](langgraph-multiagent-yelp-helper.png)

The system uses a **supervisor pattern** where one agent coordinates the work of specialized agents:

```
User Query
    ↓
Clarification Agent ────┐
    ↓                   │ (loops if unclear,
Supervisor Agent        │  max 2 attempts)
    ↓                   │
Search Agent            │
    ↓                   ↓
[Details Agent] ←─── optional based on detail level
    ↓
[Sentiment Agent] ←─── only for "reviews" level
    ↓
Summary Agent
    ↓
Final Report
```

### Agent Roles

| Agent | Purpose | When It Runs |
|-------|---------|--------------|
| **Clarification** | Extracts query, location, and detail level from user input | Always (first step) |
| **Supervisor** | Plans which agents to activate based on requirements | Always (after clarification) |
| **Search** | Finds businesses using Yelp API via Pipeline 1 | Always |
| **Details** | Fetches website content via Pipeline 2 | Only for "detailed" or "reviews" level |
| **Sentiment** | Analyzes customer reviews via Pipeline 3 | Only for "reviews" level |
| **Summary** | Synthesizes all results into readable report | Always (final step) |

## Prerequisites

### 1. Yelp Navigator Pipelines

**You must complete the [Yelp Navigator Pipeline Setup](yelp-navigator-hayhooks-guide.md) first.**

This multi-agent system depends on the Haystack pipelines being built and running:

- Pipeline 1: Business Search with NER
- Pipeline 2: Business Details Fetcher
- Pipeline 3: Reviews & Sentiment Analysis

### 2. Hayhooks Server Running

Start the Hayhooks server to expose pipeline endpoints:

```bash
cd /path/to/yelp-navigator
uv run hayhooks run --pipelines-dir pipelines
```

Verify it's running:
```bash
curl http://localhost:1416/status
```

You should see pipeline endpoints listed.

### 3. API Keys Configured

Ensure your `.env` file has:
```bash
OPENAI_API_KEY=your_openai_key_here
RAPID_API_KEY=your_rapidapi_key_here  # Must be valid and subscribed to Yelp Business Reviews API
```


## Getting Started

Open the Jupyter notebook [found here](./langgraph_multiagent_supervisor.ipynb)


### Run Examples

The notebook includes 4 example scenarios. Run them one at a time to see how the system behaves.

#### Example 1: General Search (Basic Info Only)

**What it does:** Simple query asking for basic business information only

**Expected behavior:**
- Clarification agent identifies: "Mexican restaurants", "Austin, Texas", "general" detail level
- Supervisor activates only Search Agent
- Search Agent calls Pipeline 1
- Summary Agent creates final report

---

#### Example 2: Detailed Search (With Website Info)

**What it does:** Request that needs website information

**Expected behavior:**
- Clarification agent identifies: "Italian restaurants", "San Francisco", "detailed" level
- Supervisor activates Search Agent → Details Agent
- Details Agent calls Pipeline 2 for website content
- Summary includes business info + website summaries


---

#### Example 3: Full Analysis (With Reviews)

**What it does:** Complete analysis including customer sentiment

**Expected behavior:**
- Clarification agent identifies: "coffee shops", "Portland, Oregon", "reviews" level
- Supervisor activates all agents: Search → Details → Sentiment
- Sentiment Agent calls Pipeline 3 for review analysis
- Summary includes everything: basic info, websites, and review sentiment


---

#### Example 4: Ambiguous Query

**What it does:** Tests fallback behavior with unclear input

**Expected behavior:**
- Clarification agent tries to extract info
- After 2 attempts, uses defaults to prevent infinite loop
- System proceeds with default values


## Understanding the Output

Each example shows:

1. **Agent Messages** - Step-by-step conversation showing what each agent did
2. **Search Results** - Number of businesses found and top results
3. **Agent Outputs** - Results from Details/Sentiment agents (if activated)
4. **Final Summary** - Human-readable report synthesizing all information
