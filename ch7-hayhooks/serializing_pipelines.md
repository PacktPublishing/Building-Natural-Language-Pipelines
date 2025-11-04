

## Pipeline Serialization Approaches

This project demonstrates two approaches for creating Hayhooks pipeline wrappers:

### Approach 1: Programmatic Pipeline Creation (Recommended)

This approach creates pipelines directly in Python code within the `setup()` method. This is more reliable as it ensures all components are properly imported and configured.

**Advantages:**
- Direct control over component initialization
- Better error handling during component setup
- No dependency on external YAML files
- Easier debugging and testing

**Example from `pipelines/indexing/pipeline_wrapper.py`:**

```python
def setup(self) -> None:
    """Load and configure the indexing pipeline."""
    # Import required components
    from haystack.components.fetchers import LinkContentFetcher
    from haystack.components.routers import FileTypeRouter
    # ... other imports
    
    # Create pipeline components
    link_fetcher = LinkContentFetcher()
    file_router = FileTypeRouter(mime_types=["text/plain", "application/pdf", "text/html"])
    # ... other components
    
    # Build the pipeline
    self.pipeline = Pipeline()
    
    # Add components
    self.pipeline.add_component("link_fetcher", link_fetcher)
    # ... other components
    
    # Connect components
    self.pipeline.connect("link_fetcher.streams", "html_converter.sources")
    # ... other connections
```

### Approach 2: YAML-Based Pipeline Creation

This approach uses Haystack's serialization format to define pipelines in YAML and load them dynamically. While more declarative, it can be more fragile due to component import issues.

**Advantages:**
- Declarative pipeline definition
- Easy to modify without code changes
- Good for version control and documentation
- Follows Haystack serialization standards

**Example YAML structure:**

```yaml
components:
  text_embedder:
    type: haystack.components.embedders.OpenAITextEmbedder
    init_parameters:
      model: text-embedding-3-small
      api_key:
        type: env_var
        env_vars: [OPENAI_API_KEY]

connections:
  - sender: text_embedder.embedding
    receiver: embedding_retriever.query_embedding

inputs:
  - text_embedder.text

outputs:
  - llm.replies
```

### Serialization Methods in Haystack

Haystack provides several methods for pipeline serialization:

#### Saving Pipelines

```python
from haystack import Pipeline

# Create your pipeline
pipeline = Pipeline()
# ... add components and connections

# Save to YAML string
yaml_string = pipeline.dumps()

# Save to YAML file
with open("pipeline.yml", "w") as f:
    pipeline.dump(f)
```

#### Loading Pipelines

```python
from haystack import Pipeline

# Load from YAML string
pipeline = Pipeline.loads(yaml_string)

# Load from YAML file
with open("pipeline.yml", "r") as f:
    pipeline = Pipeline.load(f)
```

#### Using Deserialization Callbacks

You can modify components during loading:

```python
from haystack.core.serialization import DeserializationCallbacks

def component_callback(component_name, component_cls, init_params):
    if component_name == "embedder":
        init_params["model"] = "different-model"

pipeline = Pipeline.loads(
    yaml_string, 
    callbacks=DeserializationCallbacks(component_callback)
)
```

## Deployment Steps

### 1. Start Hayhooks Server

```bash
# Load environment variables and start server
source .env
export HAYHOOKS_PIPELINES_DIR=./pipelines
uv run hayhooks run --host 0.0.0.0 --port 1416
```

Expected output:
```
2025-11-04 12:30:01 | INFO | Pipeline successfully added to registry - {'pipeline_name': 'indexing', ...}
2025-11-04 12:30:01 | INFO | Pipeline successfully added to registry - {'pipeline_name': 'retrieval', ...}
INFO: Uvicorn running on http://0.0.0.0:1416
```

### 2. Verify Deployment

```bash
# Check API documentation
curl http://localhost:1416/docs

# Check pipeline status
curl http://localhost:1416/status
```

### 3. Alternative: Deploy Individual Pipelines

You can deploy pipelines individually using the Hayhooks CLI:

```bash
# Deploy indexing pipeline
uv run hayhooks pipeline deploy-files -n indexing pipelines/indexing/

# Deploy retrieval pipeline
uv run hayhooks pipeline deploy-files -n retrieval pipelines/retrieval/
```

## Usage Examples

### 1. Index Documents

#### Upload Files

```bash
# Index a PDF file
uv run hayhooks pipeline run indexing --file document.pdf

# Index multiple files
uv run hayhooks pipeline run indexing --file file1.pdf --file file2.pdf

# Index from directory
uv run hayhooks pipeline run indexing --dir documents/
```

#### Index URLs

```bash
# Index web content
uv run hayhooks pipeline run indexing --param 'urls=["https://example.com/article"]'
```

#### Using cURL

```bash
# Upload file via HTTP
curl -X POST "http://localhost:1416/indexing/run" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@document.pdf"

# Index URLs via JSON
curl -X POST "http://localhost:1416/indexing/run" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/article"]}'
```

### 2. Query Documents

#### Using CLI

```bash
# Ask a question
uv run hayhooks pipeline run retrieval --param 'query="What is artificial intelligence?"'
```

#### Using cURL

```bash
# Query via HTTP
curl -X POST "http://localhost:1416/retrieval/run" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is artificial intelligence?"}'
```

#### Expected Response Format

```json
{
  "status": "success",
  "answer": "Artificial intelligence (AI) refers to...",
  "documents": [
    {
      "rank": 1,
      "content": "AI is a branch of computer science...",
      "score": 0.95,
      "metadata": {"source": "document.pdf"}
    }
  ],
  "documents_count": 3,
  "index_searched": "documents"
}
```

### 3. Python Integration

```python
import requests

# Index a document
files = {'files': open('document.pdf', 'rb')}
response = requests.post('http://localhost:1416/indexing/run', files=files)
print(response.json())

# Query documents
query_data = {'query': 'What is machine learning?'}
response = requests.post('http://localhost:1416/retrieval/run', json=query_data)
answer = response.json()
print(f"Answer: {answer['answer']}")
```

## Troubleshooting

**Common Issues:**
- **Elasticsearch not running**: `docker-compose up elasticsearch -d`
- **Missing OpenAI key**: Check your `.env` file  
- **Port conflicts**: Change `HAYHOOKS_PORT` in `.env`

#### 1. Component Import Errors

**Problem:** `Component 'haystack.components.embedders.OpenAITextEmbedder' not imported`

**Solution:** Use programmatic pipeline creation instead of YAML loading, or ensure all required packages are installed:

```bash
uv add haystack-ai
uv add elasticsearch-haystack
```

#### 2. OpenAI API Key Issues

**Problem:** `ValueError: OpenAI API key not found`

**Solution:** Ensure your API key is properly set in the `.env` file and loaded:

```bash
# Check if key is loaded
echo $OPENAI_API_KEY

# Reload environment
source .env
```

#### 3. Elasticsearch Connection Issues

**Problem:** Connection refused to Elasticsearch

**Solution:** 
```bash
# Check if Elasticsearch is running
docker-compose ps

# Restart if needed
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs elasticsearch
```

#### 4. Port Already in Use

**Problem:** `Port 1416 is already in use`

**Solution:**
```bash
# Kill existing process
lsof -i :1416
kill -9 <PID>

# Or use different port
uv run hayhooks run --port 1417
```

### Debug Mode

Enable detailed error traces:

```bash
export HAYHOOKS_SHOW_TRACEBACKS=true
uv run hayhooks run
```

### Pipeline Validation

Test pipelines individually:

```python
from pipelines.indexing.pipeline_wrapper import PipelineWrapper as IndexingWrapper
from pipelines.retrieval.pipeline_wrapper import PipelineWrapper as RetrievalWrapper

# Test indexing
indexing = IndexingWrapper()
indexing.setup()
print("Indexing pipeline loaded successfully")

# Test retrieval
retrieval = RetrievalWrapper() 
retrieval.setup()
print("Retrieval pipeline loaded successfully")
```

## Advanced Configuration

### Custom Elasticsearch Configuration

Modify `docker-compose.yml` for production settings:

```yaml
services:
  elasticsearch:
    environment:
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"  # Increase memory
      - cluster.name=production-cluster
      - bootstrap.memory_lock=true
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
      - ./config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml
```

### Pipeline Customization

#### Modify Component Parameters

Edit pipeline wrappers to adjust model parameters:

```python
# In retrieval pipeline_wrapper.py
ranker = SentenceTransformersSimilarityRanker(
    model="BAAI/bge-reranker-large",  # Use larger model
    top_k=5  # Return more documents
)

llm = OpenAIGenerator(
    model="gpt-4",  # Use GPT-4 instead of mini
    temperature=0.1  # Lower temperature for consistency
)
```

### Environment-Specific Configuration

Create environment-specific `.env` files:

```bash
# .env.development
ELASTICSEARCH_INDEX=documents-dev
HAYHOOKS_PORT=1416

# .env.production  
ELASTICSEARCH_INDEX=documents-prod
HAYHOOKS_PORT=8000
```

### Monitoring and Logging

Enable structured logging:

```python
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```

Add health check endpoints:

```python
# In pipeline_wrapper.py
def health_check(self):
    """Check if pipeline components are healthy."""
    try:
        # Test document store connection
        self.document_store._client.ping()
        return {"status": "healthy", "timestamp": datetime.utcnow()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```


## Additional Resources

- [Hayhooks Documentation](https://docs.haystack.deepset.ai/docs/hayhooks)
- [Haystack Pipeline Serialization](https://docs.haystack.deepset.ai/docs/serialization)
- [Elasticsearch Haystack Integration](https://docs.haystack.deepset.ai/docs/elasticsearch-document-store)
- [OpenAI Components](https://docs.haystack.deepset.ai/docs/embedders)


## License

This project is part of the "Building Natural Language Pipelines" book by Packt Publishing.