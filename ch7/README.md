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

**Generate a secure API key** (recommended):
```bash
# macOS/Linux
openssl rand -hex 32
```

Enter your key in the `.env` file

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys:
# OPENAI_API_KEY=your_actual_openai_key
# RAG_API_KEY=your_secret_api_key_for_authentication 
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
  -e OPENAI_API_KEY=your_actual_openai_key \
  -e RAG_API_KEY=your_secret_api_key \
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
- **POST /query**: Submit queries to the RAG system (**requires authentication**)
- **GET /docs**: Interactive API documentation (Swagger UI)

## 🔐 API Authentication

The `/query` endpoint is protected with API key authentication to prevent unauthorized access.

### Setting Up Authentication

1. **Generate a secure API key**:
```bash
# Generate a random 32-byte hex string (recommended)
openssl rand -hex 32
```

2. **Add to your `.env` file**:
```bash
RAG_API_KEY=<your secret>
```

3. **For Docker deployment**, pass it as an environment variable:
```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e RAG_API_KEY=your-secret-key \
  hybrid-rag-api
```

### Using the Authenticated API

Include the API key in the `X-API-Key` header with every request to `/query`:

**cURL Example**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"query": "What is retrieval-augmented generation?"}'
```

**Python Example**:
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": "your-secret-key"
    },
    json={"query": "What is retrieval-augmented generation?"}
)

print(response.json())
```

**JavaScript/Fetch Example**:
```javascript
fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-secret-key'
  },
  body: JSON.stringify({
    query: 'What is retrieval-augmented generation?'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### Security Notes

- ✅ Only `/query` endpoint requires authentication
- ✅ All other endpoints (`/`, `/health`, `/info`, `/docs`) remain publicly accessible
- ✅ Invalid or missing API keys return `401 Unauthorized`
- ⚠️ **Never commit your API key to version control**
- ⚠️ Use different keys for development, staging, and production
- ⚠️ Store production keys in secure secret management systems (GitHub Secrets, AWS Secrets Manager, etc.)


## Project Structure

Project structure can be found [here](./PROJECT_STRUCTURE.md)

## Configuration

All configuration is handled via environment variables. See `.env.example` for all available options:

### Required Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `RAG_API_KEY`: Secret key for API authentication (required)

### Optional Variables
- `QDRANT_PATH`: Qdrant storage directory path (default: `./qdrant_storage`)
- `QDRANT_INDEX`: Index name for documents (default: `documents`)
- `EMBEDDER_MODEL`: Embedding model (default: `text-embedding-3-small`)
- `LLM_MODEL`: Language model (default: `gpt-4o-mini`)
- `RANKER_MODEL`: Reranker model (default: `BAAI/bge-reranker-base`)
- `TOP_K`: Number of documents to retrieve (default: `3`)
- `API_HOST`: API host address (default: `0.0.0.0`)
- `API_PORT`: API port number (default: `8000`)
- `DEBUG`: Enable debug mode (default: `false`)

## Development Workflow

1. **Local First**: Develop and test locally using the scripts
2. **Test Thoroughly**: Use the comprehensive test suite
3. **Docker Testing**: Test with Docker Compose before deployment
4. **Production**: Deploy using Docker in your preferred environment

## Troubleshooting

### Common Issues

1. **401 Unauthorized on `/query` endpoint**:
   - Verify `RAG_API_KEY` is set in your `.env` file
   - Ensure you're including the `X-API-Key` header in your requests
   - Check that the key in the header matches the one in your `.env` file

2. **OpenAI API errors**:
   - Verify your `OPENAI_API_KEY` is set correctly in `.env`
   - Check your OpenAI account has credits

3. **No documents found**:
   - Run indexing first: `./scripts/run_indexing.sh`
   - Check if Qdrant storage directory exists: `ls -la ./qdrant_storage`

4. **API won't start - missing RAG_API_KEY**:
   - Add `RAG_API_KEY=your-secret-key` to your `.env` file
   - Generate a secure key: `openssl rand -hex 32`

5. **Import errors in development**:
   - Make sure you're running from the project root
   - Use `uv run python -m src.app` instead of direct imports

### Logs and Debugging

- API logs: Check terminal output when running `./scripts/run_api.sh`
- Docker logs: `docker-compose logs api`
- Enable debug mode: Set `DEBUG=true` in `.env` 


