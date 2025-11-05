# Hybrid RAG Application

A production-ready Hybrid Retrieval-Augmented Generation (RAG) application using Haystack, Elasticsearch, and OpenAI.

## Features

- **Hybrid Retrieval**: Combines BM25 (keyword-based) and embedding-based (semantic) search
- **FastAPI REST API**: Clean, documented API with health checks and error handling
- **Elasticsearch Integration**: Scalable document storage and search
- **OpenAI Integration**: State-of-the-art embeddings and language generation
- **Docker Support**: Full containerization with Docker Compose
- **Local Development**: Script-based workflow for easy local development

## Quick Start

### Local Development (Recommended first)

1. **Setup environment**:
```bash
uv sync
source .venv/bin/activate

./scripts/setup_local.sh
```

2. **Configure environment**:
```bash
# Edit .env file and add your OpenAI API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=your_actual_key
```

3. **Create and start Elasticsearch**:
```bash
docker-compose up -d elasticsearch
```

```bash
docker-compose up -d elasticsearch
```

4. **Run indexing**:
```bash
./scripts/run_indexing.sh
```

5. **Start API**:
```bash
./scripts/run_api.sh
```

6. **Test the API**:
```bash
uv run python tests/test_api.py
```

### Docker Deployment

1. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=your_actual_key
```

2. **Run full stack**:
```bash
docker-compose up -d
```

3. **Test**:
```bash
# Wait for services to be ready
uv run python tests/test_api.py wait

# Run tests
uv run python tests/test_api.py
```

## API Endpoints

- **GET /**:  Basic API information
- **GET /health**: Health check with component status
- **GET /info**: Configuration and model information
- **POST /query**: Submit queries to the RAG system
- **GET /docs**: Interactive API documentation (Swagger UI)


## Project Structure

Project structure can be found [here](./PROJECT_STRUCTURE.md)

## Configuration

All configuration is handled via environment variables. See `.env.example` for all available options:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `ELASTICSEARCH_HOST`: Elasticsearch connection URL
- `ELASTICSEARCH_INDEX`: Index name for documents
- Model configurations (embedder, LLM, ranker models)
- API settings (host, port, debug mode)

## Development Workflow

1. **Local First**: Develop and test locally using the scripts
2. **Test Thoroughly**: Use the comprehensive test suite
3. **Docker Testing**: Test with Docker Compose before deployment
4. **Production**: Deploy using Docker in your preferred environment

## Troubleshooting

### Common Issues

1. **Elasticsearch not available**:
   - Check if Elasticsearch is running: `curl http://localhost:9200/_cat/health`
   - Start with: `docker run -d -p 9200:9200 -e discovery.type=single-node docker.elastic.co/elasticsearch/elasticsearch:8.11.1`

2. **OpenAI API errors**:
   - Verify your API key is set correctly in `.env`
   - Check your OpenAI account has credits

3. **No documents found**:
   - Run indexing first: `./scripts/run_indexing.sh`
   - Check Elasticsearch index: `curl http://localhost:9200/documents/_count`

4. **Import errors in development**:
   - Make sure you're running from the project root
   - Use `uv run python -m src.app` instead of direct imports

### Logs and Debugging

- API logs: Check terminal output when running `./scripts/run_api.sh`
- Docker logs: `docker-compose logs api`
- Elasticsearch logs: `docker-compose logs elasticsearch`
- Enable debug mode: Set `DEBUG=true` in `.env` 


