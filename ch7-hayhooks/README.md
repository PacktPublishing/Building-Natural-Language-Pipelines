# Chapter 7 Deploying Haystack-based applications  

 
In this chapter you will learn about how to deploy multiple Haystack pipelines as REST API services that can interact with one another using Hayhooks, providing production-ready endpoints for document indexing and intelligent question answering. This is Part II in chapter 7, covering an advanced case where you will learn to deploy an indexing and advanced retrieval pipelines that can dynamically upload a PDF and web urls and answer questions about the uploaded material. In [Part I](../ch7/README.md) we learn about a simpler case where we deploy a Haystack pipeline as a REST API using FastAPI and dockerize the application.

## 🔒 Security

This deployment includes nginx reverse proxy with authentication. Your Hayhooks endpoints are secured and not accessible to the world.

See [SECURITY.md](SECURITY.md) for complete security setup and configuration details.

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

# Hayhooks Configuration
HAYHOOKS_HOST=0.0.0.0
HAYHOOKS_PORT=1416
HAYHOOKS_PIPELINES_DIR=./pipelines
HAYHOOKS_SHOW_TRACEBACKS=true
```

2. **Setup Authentication** (Required for production):
```bash
# Generate credentials for API access
./scripts/generate_password.sh
```

3. **Run Hayhooks**:

**Option A: Local Development (⚠️ NOT password protected)**
```bash
# Runs on http://localhost:1416 - open to anyone with network access
# Use this for local testing only, NOT for production
uv run hayhooks run
```

You can then visit [http://0.0.0.0:1416/docs#/](http://0.0.0.0:1416/docs#/) and test the endpoints.


**Option B: Using Docker Compose with nginx Security (🔒 Recommended for production)**

```bash
# Start both Hayhooks and nginx with authentication
docker-compose up -d

# Check logs
docker-compose logs -f

# Test the secured API
./scripts/test_secured_api.sh

# Access protected endpoints with authentication
curl -u username:password http://localhost:8080/status
```

You can then visit [http://localhost:8080/docs](http://localhost:8080/docs), enter your passowrd and test the endpoints.


``` bash
# Stop services
docker-compose down
```

**Option C: Using Docker (Single Container, No Security)**

1. **Build the Docker image**:
```bash
docker build -t hayhooks-index-rag .
```

2. **Run the container**:
```bash
docker run -d \
  --name hayhooks-rag \
  -p 1416:1416 \
  -e OPENAI_API_KEY=your_actual_key_here \
  -v $(pwd)/qdrant_storage:/app/qdrant_storage \
  hayhooks-index-rag
```

3. **Check logs**:
```bash
docker logs -f hayhooks-rag
```

4. **Test the API**:
```bash
# Verify the server is running (unsecured)
curl http://localhost:1416/status
```

You can then visit [http://0.0.0.0:1416/docs#/](http://0.0.0.0:1416/docs#/) and test the endpoints.


5. **Stop the container**:
```bash
docker stop hayhooks-rag
docker rm hayhooks-rag
```

## Docker Deployment Guide

### Understanding the Docker Setup

The Docker container packages all dependencies and pipelines for easy deployment:

- **Port Mapping**: Container port `1416` maps to host `localhost:1416`
- **Volume Mounting**: Local `qdrant_storage` directory persists vector data
- **Environment Variables**: OpenAI API key passed securely via `-e` flag

### Docker Commands Reference

```bash
# Build the image
docker build -t hayhooks-index-rag .

# Run container (basic)
docker run -d \
  --name hayhooks-rag \
  -p 1416:1416 \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/qdrant_storage:/app/qdrant_storage \
  hayhooks-index-rag

# View logs in real-time
docker logs -f hayhooks-rag

# View last 100 lines of logs
docker logs --tail 100 hayhooks-rag

# Check container status
docker ps

# Stop container
docker stop hayhooks-rag

# Start existing container
docker start hayhooks-rag

# Remove container
docker rm hayhooks-rag

# Access container shell for debugging
docker exec -it hayhooks-rag /bin/bash

# Rebuild image (after code changes)
docker build --no-cache -t hayhooks-index-rag .
```

### Advanced Docker Configuration

**Run with custom port:**
```bash
docker run -d \
  --name hayhooks-rag \
  -p 8000:1416 \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/qdrant_storage:/app/qdrant_storage \
  hayhooks-index-rag
```


**Run with additional environment variables:**
```bash
docker run -d \
  --name hayhooks-rag \
  -p 1416:1416 \
  -e OPENAI_API_KEY=your_key \
  -e QDRANT_API_KEY=your_qdrant_key \
  -e QDRANT_HOST_URL=your_qdrant_url \
  -v $(pwd)/qdrant_storage:/app/qdrant_storage \
  hayhooks-index-rag
```

### Troubleshooting Docker Deployment

**Issue**: Port already in use
```bash
# Find process using port 1416
lsof -i :1416

# Kill the process
kill -9 <PID>

# Or use a different port
docker run -p 8080:1416 ...
```

**Issue**: Container exits immediately
```bash
# Check logs for errors
docker logs hayhooks-rag

# Common causes:
# - Missing OPENAI_API_KEY
# - Port conflict
# - Invalid pipeline configuration
```

**Issue**: Changes not reflected after rebuild
```bash
# Stop and remove container
docker stop hayhooks-rag && docker rm hayhooks-rag

# Rebuild without cache
docker build --no-cache -t hayhooks-index-rag .

# Run new container
docker run -d --name hayhooks-rag -p 1416:1416 \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/qdrant_storage:/app/qdrant_storage \
  hayhooks-index-rag
```

**Issue**: Permission denied on qdrant_storage
```bash
# Create directory with proper permissions
mkdir -p qdrant_storage
chmod 755 qdrant_storage
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

### Using cURL

#### Index a Document
```bash
curl -X POST "http://localhost:1416/indexing/run" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/article"]}'
```

#### Ask a Question  
```bash
curl -X POST "http://localhost:1416/hybrid_rag/run" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the benefits of AI?"}'
```

#### OpenAI-Style Chat
```bash
curl -X POST "http://localhost:1416/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hybrid_rag",
    "messages": [{"role": "user", "content": "Explain machine learning"}]
  }'
```

### Using Python (Programmatic Access)

Hayhooks provides a Python client for programmatic access to your deployed pipelines:

```python
import requests

# Base URL for your Hayhooks server
BASE_URL = "http://localhost:1416"

# Index documents
response = requests.post(
    f"{BASE_URL}/indexing/run",
    json={"urls": ["https://example.com/article"]}
)
print(response.json())

# Query the RAG pipeline
response = requests.post(
    f"{BASE_URL}/hybrid_rag/run",
    json={"query": "What are the benefits of AI?"}
)
print(response.json())

# OpenAI-compatible chat completions
response = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={
        "model": "hybrid_rag",
        "messages": [{"role": "user", "content": "Explain machine learning"}]
    }
)
print(response.json())
```

### Using the Hayhooks CLI

You can also run pipelines directly from the command line:

```bash
# Run a query through the RAG pipeline
hayhooks pipeline run hybrid_rag --param 'query="What is AI?"'

# Index documents with file upload
hayhooks pipeline run indexing --file document.pdf

# Index multiple files
hayhooks pipeline run indexing --file file1.pdf --file file2.pdf

# Index a directory of files
hayhooks pipeline run indexing --dir ./documents
```

## Overview

This project consists of two main pipelines:

1. **Indexing Pipeline**: Processes documents (PDFs, web content) and stores them with embeddings in Qdrant
2. **Retrieval Pipeline**: Performs hybrid RAG (BM25 + embeddings) to answer questions based on indexed documents

Both pipelines are exposed through Hayhooks as REST API endpoints, making them easy to integrate into web applications or other systems.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
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

## Troubleshooting

### Common Issues

#### 1. Pipeline Loading Errors

**Error**: `'dict' object has no attribute 'resolve_value'` in DocumentWriter
- **Cause**: Configuration issues with document store
- **Solution**: Ensure document store is properly configured in pipeline YAML files

**Error**: `ModuleNotFoundError: No module named 'nltk'` or similar import errors
- **Cause**: Missing optional dependencies
- **Solution**: Install missing packages:
  ```bash
  uv add nltk>=3.9.1 lxml_html_clean pypdf>=6.1.3
  ```

#### 2. Document Store Issues

**Error**: Connection or storage issues
- **Solution**: Ensure Qdrant storage directory exists and has proper permissions:
  ```bash
  mkdir -p ./qdrant_storage
  ```

#### 3. OpenAI API Issues

**Error**: Invalid API key or authentication errors
- **Solution**: Verify your OpenAI API key is correctly set in `.env`

#### 4. Qdrant Concurrent Access Issues

**Error**: `Storage folder ./qdrant_storage is already accessed by another instance of Qdrant client`
- **Cause**: Running the indexing pipeline and then attempting to run the RAG pipeline causes a concurrent access error because both pipelines try to access the same local Qdrant storage folder
- **Impact**: You'll see this error when trying to use the `/hybrid_rag/run` endpoint after indexing documents
- **Solution**: Modify both pipeline serialization scripts to use cloud-based Qdrant instead of local storage:
  
  In `pipelines/indexing_pipeline_serialization.py` and `pipelines/rag_pipeline_serialization.py`, replace:
  ```python
  # Initialize document store (same path as indexing)
  document_store = QdrantDocumentStore(
      path="./qdrant_storage",
      index="documents",
      embedding_dim=1536,  # text-embedding-3-small dimension
      recreate_index=False,
      use_sparse_embeddings=True  # Enable sparse embeddings for BM25-like retrieval
  )
  ```
  
  With cloud-based configuration:
  ```python
  # Initialize document store (cloud-based for concurrent access)
  document_store = QdrantDocumentStore(
      url="your_qdrant_url",  # e.g., "https://xyz-example.eu-central.aws.cloud.qdrant.io:6333"
      api_key=Secret.from_env_var("QDRANT_API_KEY"),
      index="documents",
      embedding_dim=1536,
      recreate_index=False,
      use_sparse_embeddings=True
  )
  ```
  
  Then add to your `.env` file:
  ```bash
  QDRANT_API_KEY=your_qdrant_api_key_here
  QDRANT_HOST_URL=your_qdrant_url_here
  ```

#### 5. MPS Device Compatibility Issues

**Warning**: `MPS backend is not available` or errors related to device configuration
- **Cause**: The serialized pipeline YAML files may have `device: mps` set for the ranker component, but MPS (Metal Performance Shaders) is only available on Apple Silicon Macs and may not be supported in all environments
- **Impact**: Pipeline fails to load or run with device-related errors
- **Solution**: Modify the device configuration in the YAML files to use CPU instead:
  
  In `pipelines/hybrid_rag/rag.yml`, find the ranker component's device configuration and change it to:
  ```yaml
  device:
    device: cpu
    type: single
  ```
  
  This ensures compatibility across all environments including Docker containers and cloud deployments.


## Advanced Usage

For detailed instructions on:
- Pipeline wrapper development
- YAML serialization
- Docker deployment  
- Performance tuning
- Custom endpoints
- Production configuration

[Review pipeline serialization and deployment steps](./serializing_pipelines.md)