# Chapter 7 Deploying Haystack-based applications  

 
In this chapter you will learn about how to deploy a Haystack retriever pipeline as a REST API Endpoint with FastAPI. This is part I - deploying a retrieval pipeline from a prepopulated document store. [Part II](../ch7-hayhooks/README.md) is an advanced case where you will learn to deploy an indexing and advanced retrieval pipelines that can dynamically upload a PDF and web urls and answer questions about the uploaded material.

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

3. **Run indexing**:
```bash
./scripts/run_indexing.sh
```

4. **Start API**:
```bash
./scripts/run_api.sh
```

5. **Test the API**:
```bash
uv run python tests/test_api.py
```

### Docker Deployment

#### Build and Run (Single Container)

1. **Build the Docker image**:
```bash
docker build -t hybrid-rag-api .
```

2. **Run the container**:
```bash
docker run -d \
  --name hybrid-rag \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_actual_key_here \
  hybrid-rag-api
```

3. **Check logs**:
```bash
docker logs -f hybrid-rag
```

4. **Test the API**:
```bash
# Once container shows "✅ Indexing complete!" and "🚀 Starting API server..."
curl http://localhost:8000/health
```

5. **Stop the container**:
```bash
docker stop hybrid-rag
docker rm hybrid-rag
```

**Note**: The Docker container automatically runs the indexing pipeline on startup before launching the API. This takes a few minutes depending on the size of your data.

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
- `QDRANT_PATH`: Qdrant storage directory path
- `QDRANT_INDEX`: Index name for documents
- Model configurations (embedder, LLM, ranker models)
- API settings (host, port, debug mode)

## Development Workflow

1. **Local First**: Develop and test locally using the scripts
2. **Test Thoroughly**: Use the comprehensive test suite
3. **Docker Testing**: Test with Docker Compose before deployment
4. **Production**: Deploy using Docker in your preferred environment

## Troubleshooting

### Common Issues

1. **OpenAI API errors**:
   - Verify your API key is set correctly in `.env`
   - Check your OpenAI account has credits

2. **No documents found**:
   - Run indexing first: `./scripts/run_indexing.sh`
   - Check if Qdrant storage directory exists: `ls -la ./qdrant_storage`

4. **Import errors in development**:
   - Make sure you're running from the project root
   - Use `uv run python -m src.app` instead of direct imports

### Logs and Debugging

- API logs: Check terminal output when running `./scripts/run_api.sh`
- Docker logs: `docker-compose logs api`
- Enable debug mode: Set `DEBUG=true` in `.env` 


