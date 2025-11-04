# Docker Usage Guide

This guide explains how to run the Hybrid RAG application using Docker.

## Prerequisites

1. **Docker and Docker Compose** installed on your system
2. **Environment file** (`.env`) with required API keys:
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key    # Optional
   WANDB_API_KEY=your_wandb_api_key      # Optional
   ```

## Option 1: Full Stack (Recommended)

Runs Elasticsearch, indexing, and API services together:

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs api
docker-compose logs indexing

# Stop all services
docker-compose down
```

**Services started:**
- **Elasticsearch** on `http://localhost:9200`
- **Indexing service** (runs once to populate data)
- **API service** on `http://localhost:8000`

## Option 2: Local Development

If you already have Elasticsearch running locally:

```bash
# Start only the API (assumes Elasticsearch on localhost:9200)
docker-compose -f docker-compose.local.yml up -d

# View logs
docker-compose -f docker-compose.local.yml logs api

# Stop
docker-compose -f docker-compose.local.yml down
```

## API Endpoints

Once running, access:
- **API Root:** `http://localhost:8000`
- **Health Check:** `http://localhost:8000/health`
- **API Documentation:** `http://localhost:8000/docs`
- **Query Endpoint:** `POST http://localhost:8000/query`

## Example Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Query the RAG System
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the benefits of AI?"}'
```

## Troubleshooting

### Build Issues
```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Check Elasticsearch
```bash
# Verify Elasticsearch is running
curl http://localhost:9200/_cat/health

# Check document count
curl http://localhost:9200/documents/_count
```

### View Container Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs elasticsearch
docker-compose logs indexing
docker-compose logs api
```

### Port Conflicts
If port 8000 or 9200 is already in use:
```bash
# Find processes using the port
lsof -ti:8000
lsof -ti:9200

# Kill processes if needed
kill -9 <process_id>
```

## Development Notes

- The **local development setup** (`docker-compose.local.yml`) mounts source code as read-only volumes for hot reloading
- The **full stack setup** (`docker-compose.yml`) includes data persistence via Docker volumes
- Environment variables are safely handled with default empty values for optional keys
- All services use `uv run` for consistent Python environment management

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | - | OpenAI API key for embeddings and LLM |
| `TAVILY_API_KEY` | ❌ No | - | Optional Tavily API key |
| `WANDB_API_KEY` | ❌ No | - | Optional Weights & Biases API key |
| `ELASTICSEARCH_HOST` | ❌ No | `http://localhost:9200` | Elasticsearch connection URL |
| `ELASTICSEARCH_INDEX` | ❌ No | `documents` | Index name for document storage |
| `DEBUG` | ❌ No | `false` | Enable debug mode |