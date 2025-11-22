# LangGraph Multi-Agent Supervisor Guide

## Overview

A multi-agent system that searches for businesses on Yelp and generates comprehensive reports. The system coordinates specialized agents to understand your query, search for businesses, gather details, and create summaries.

### Example

**Query:** "Mexican restaurants in Austin, Texas with customer reviews"

**Result:** A report with restaurant recommendations, website info, and sentiment analysis from reviews

## How It Works

```
User Query → Clarification → Search → [Details] → [Sentiment] → Summary → Approval
```

**Agents:**
- **Clarification**: Extracts query, location, detail level
- **Search**: Finds businesses (Pipeline 1)
- **Details**: Fetches websites (Pipeline 2) - runs for "detailed" or "reviews" level
- **Sentiment**: Analyzes reviews (Pipeline 3) - runs only for "reviews" level
- **Summary**: Creates final report
- **Supervisor**: Reviews and approves (or requests revisions)

## Prerequisites

1. Complete [Yelp Navigator Pipeline Setup](./yelp-navigator-hayhooks-guide.md)
2. Start Hayhooks server: `sh start_hayhooks.sh`

## Getting Started

Open `langgraph_multiagent_supervisor.ipynb` and run the examples

