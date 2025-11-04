# Hayhooks MCP - Indexing & Hybrid RAG Deployment

This project demonstrates how to deploy Haystack pipelines as REST API services using Hayhooks, providing production-ready endpoints for document indexing and intelligent question answering.


## Quick Start

1. **Setup Environment**:
```bash
# Install dependencies
uv sync

# Copy .env.example and add your openAI API key
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:


```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_actual_openai_api_key_here

# Elasticsearch Configuration
ELASTICSEARCH_HOSTS=http://localhost:9200
ELASTICSEARCH_INDEX=documents

# Hayhooks Configuration
HAYHOOKS_HOST=0.0.0.0
HAYHOOKS_PORT=1416
HAYHOOKS_PIPELINES_DIR=./pipelines
HAYHOOKS_SHOW_TRACEBACKS=true
```

2. **Start Elasticsearch**

```bash
# Create and Start Elasticsearch using Docker Compose
docker-compose up -d elasticsearch

# Running
docker-compose up -d elasticsearch

# Verify Elasticsearch is running
curl -X GET "localhost:9200/_cluster/health?pretty"
```

Expected response:

```json
{
  "cluster_name" : "docker-cluster",
  "status" : "green",
  "timed_out" : false,
  "number_of_nodes" : 1,
  "number_of_data_nodes" : 1,
  "active_primary_shards" : 0,
  "active_shards" : 0,
  "relocating_shards" : 0,
  "initializing_shards" : 0,
  "unassigned_shards" : 0,
  "delayed_unassigned_shards" : 0,
  "number_of_pending_tasks" : 0,
  "number_of_in_flight_fetch" : 0,
  "task_max_waiting_in_queue_millis" : 0,
  "active_shards_percent_as_number" : 100.0
}
```

3. **Run Hayhookst**:
```bash
uv run hayhooks run
```

## API Endpoints

Once deployed, your pipelines are available at:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/indexing/run` | POST | Index documents from URLs or files |
| `/hybrid_rag/run` | POST | Answer questions using RAG |
| `/v1/chat/completions` | POST | OpenAI-compatible chat interface |
| `/docs` | GET | Interactive API documentation |
| `/status` | GET | Server and pipeline status |

## Usage Examples

### Index a Document
```bash
curl -X POST "http://localhost:1416/indexing/run" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/article"]}'
```

### Ask a Question  
```bash
curl -X POST "http://localhost:1416/hybrid_rag/run" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the benefits of AI?"}'
```

### OpenAI-Style Chat
```bash
curl -X POST "http://localhost:1416/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hybrid_rag",
    "messages": [{"role": "user", "content": "Explain machine learning"}]
  }'
```

## Overview

This project consists of two main pipelines:

1. **Indexing Pipeline**: Processes documents (PDFs, web content) and stores them in Elasticsearch with embeddings
2. **Retrieval Pipeline**: Performs hybrid RAG (BM25 + embeddings) to answer questions based on indexed documents

Both pipelines are exposed through Hayhooks as REST API endpoints, making them easy to integrate into web applications or other systems.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Web Files     │    │  Indexing        │    │   Elasticsearch     │
│   PDF Files     ├───►│  Pipeline        ├───►│   Document Store    │
│   URLs          │    │  (Hayhooks)      │    │                     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                                          │
┌─────────────────┐    ┌──────────────────┐              │
│   Questions     │    │  Retrieval       │◄─────────────┘
│   Queries       ├───►│  Pipeline        │
│                 │    │  (Hayhooks)      │
└─────────────────┘    └──────────────────┘
```

### Pipeline Components

#### Indexing Pipeline
- **LinkContentFetcher**: Fetches content from URLs
- **FileTypeRouter**: Routes files based on MIME type (PDF, HTML, text)
- **Document Converters**: Convert PDFs and HTML to text
- **DocumentCleaner**: Removes extra whitespace and empty lines
- **DocumentSplitter**: Splits documents into chunks
- **OpenAIDocumentEmbedder**: Creates embeddings using OpenAI
- **DocumentWriter**: Stores documents in Elasticsearch

#### Retrieval Pipeline
- **OpenAITextEmbedder**: Embeds user queries
- **ElasticsearchEmbeddingRetriever**: Dense retrieval using embeddings
- **ElasticsearchBM25Retriever**: Sparse retrieval using BM25
- **DocumentJoiner**: Combines results from both retrievers
- **SentenceTransformersSimilarityRanker**: Re-ranks documents for relevance
- **PromptBuilder**: Creates prompts with retrieved context
- **OpenAIGenerator**: Generates answers using GPT

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker and Docker Compose
- OpenAI API key


## Project Structure

```
hayhooks-mcp/
├── docker-compose.yml             # Docker services
├── pipelines/                        # Pipeline wrappers
│   ├── indexing/
│   │   └── pipeline_wrapper.py      # Indexing API wrapper
│   └── hybrid_rag/
│       └── pipeline_wrapper.py      # RAG API wrapper
```

## What This Provides

### Document Indexing API
- **URL Indexing**: Fetch and index web content
- **File Upload**: Index PDF, HTML, and text files  
- **Batch Processing**: Handle multiple documents at once
- **Smart Chunking**: Sentence-based splitting with overlap

### Hybrid RAG Query API  
- **Intelligent Retrieval**: BM25 + embedding-based search
- **Reranking**: Advanced relevance scoring
- **Contextual Answers**: GPT-powered response generation
- **Source Attribution**: Track document sources

### OpenAI Compatibility
- **Chat Completions**: `/v1/chat/completions` endpoint
- **Easy Integration**: Works with existing OpenAI clients
- **Streaming Support**: Real-time response streaming


## Features

- **Production Ready**: Docker deployment with health checks
- **Auto Documentation**: Swagger/OpenAPI docs generation  
- **Smart Retrieval**: Hybrid BM25 + embedding search
- **Fast Processing**: Optimized pipeline execution
- **Error Handling**: Comprehensive error reporting
- **Scalable**: Horizontal scaling support
- **Extensible**: Easy to add new endpoints

## Advanced Usage

For detailed instructions on:
- Pipeline wrapper development
- YAML serialization
- Docker deployment  
- Performance tuning
- Custom endpoints
- Production configuration

[Review pipeline serialization and deployment steps](./serializing_pipelines.md)