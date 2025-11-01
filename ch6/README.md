# Chapter 6: Setting up a Reproducible Q&A Pipeline

This chapter covers building reproducible workflows for question and answer systems using Elasticsearch, Haystack, and vector embeddings.

## 🚀 Quick Start Guide

Follow these steps to get up and running:

### Step 1: Install Prerequisites

**Install Docker:**
```bash
brew install docker
brew install docker-compose
brew install --cask docker
```

**Install uv (Python package manager):**
```bash
pip install uv
```

### Step 2: Set Up Python Environment

**Install dependencies and activate environment:**
```bash
# Install all dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate
```

### Step 3: Configure API Keys

Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=your_openai_key_here
```

Get your OpenAI API key at [OpenAI's platform](https://platform.openai.com)

### Step 4: Set Up VS Code (Recommended)

**Open this chapter folder in VS Code:**
- Open VS Code
- File → Open Folder → Select this `ch6` folder
- Select the `.venv` environment as your Python interpreter

**For Jupyter notebooks:**
- Open any `.ipynb` file
- Click the kernel picker (top right)
- Select the `.venv` environment

### Step 5: Start Elasticsearch

**Start Elasticsearch container:**
```bash
# Start in detached mode
docker-compose up -d

# Run the indexing script
uv run python scripts/indexing.py

# Verify it's running (should show cluster health)
curl -X GET "localhost:9200/_cat/health?v"
```

---

## 📚 Elasticsearch Document Indexing Workflow

Now you'll index multiple data sources with vector embeddings for semantic search.

### Step 1: Prepare Data Sources

The indexing pipeline processes four types of data sources:

1. **Web content**: Fetches from `https://haystack.deepset.ai/blog/haystack-2-release`
2. **Text file**: `data_for_indexing/haystack_intro.txt`
3. **PDF file**: `data_for_indexing/howpeopleuseai.pdf` 
4. **CSV file**: `data_for_indexing/llm_models.csv`

Create the sample data files by running:

```bash
cd scripts
uv run python dummy_data.py
```

### Step 2: Run the Indexing Pipeline

Execute the indexing script to process all data sources and store them in Elasticsearch:

```bash
cd scripts
uv run python indexing.py
```

**Expected Output:**
```
Running unified indexing pipeline for web, local files, and CSV...
Error processing document [...]. Keeping it, but skipping cleaning. Error: [...]
Error processing document [...]. Keeping it, but skipping splitting. Error: [...]
Batches: 100%|████████████████| 5/5 [00:00<00:00,  6.21it/s]
```

The pipeline will:
- Fetch and process web content from the Haystack blog
- Convert and chunk the PDF document into readable segments
- Process text and CSV files
- Generate 384-dimensional vector embeddings for all content
- Store approximately 133 documents in Elasticsearch

### Step 3: Verify Documents are Loaded

Check that documents have been successfully indexed:

```bash
# Get total document count
curl -X GET "localhost:9200/default/_count"

# Expected output: {"count":133,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0}}

# View document breakdown by source
curl -X GET "localhost:9200/default/_search?size=0&pretty" -H "Content-Type: application/json" -d '{
  "aggs": {
    "sources": {
      "terms": {
        "field": "file_path.keyword", 
        "size": 10,
        "missing": "web_content"
      }
    }
  }
}'

# Sample a document to verify embeddings
curl -X GET "localhost:9200/default/_search?size=1&pretty"
```

**Expected Document Distribution:**
- ~118 documents from `howpeopleuseai.pdf`
- ~13 documents from web content  
- 1 document from `haystack_intro.txt`
- 1 document from `llm_models.csv`

### Step 4: Clean Up (Optional)

To stop the Elasticsearch container and clean up:

```bash
# Stop the container
docker-compose down

# Remove the index (if you want to start fresh)
curl -X DELETE "localhost:9200/default"
```

### Troubleshooting

**Issue: Duplicate document errors**
```bash
# Solution: Clear the index and recreate with proper mappings
curl -X DELETE "localhost:9200/default"
curl -X PUT "localhost:9200/default" -H "Content-Type: application/json" -d '{
  "mappings": {
    "properties": {
      "content": {"type": "text"},
      "content_type": {"type": "keyword"}, 
      "id": {"type": "keyword"},
      "embedding": {"type": "dense_vector", "dims": 384}
    }
  }
}'
```

**Issue: PDF not found warnings**
- Ensure you're running from the correct directory
- Verify the PDF file exists in `data_for_indexing/howpeopleuseai.pdf`
- Run `uv run python dummy_data.py` to set up correct file paths



