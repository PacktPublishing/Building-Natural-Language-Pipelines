# Chapter 6: Setting up a Reproducible Q&A Pipeline

This chapter covers building reproducible workflows for question and answer systems using Elasticsearch, Haystack, and vector embeddings.

## Setup

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
```

---

## 📚 Elasticsearch Document Indexing Workflow

Now you'll index multiple data sources with vector embeddings for semantic search.

### Step 1: Prepare Data Sources

The indexing pipeline processes four types of data sources:

1. **Web content**: Fetches from 
- `https://www.bbc.com/news/articles/c2l799gxjjpo`
- `https://www.brookings.edu/articles/how-artificial-intelligence-is-transforming-the-world/`
2. **PDF file**: `data_for_indexing/howpeopleuseai.pdf` 

### Step 2: Generate Synthetic data

Execute

```bash
cd jupyter-notebooks
uv run python scripts/synthetic_data_generation/sdg_html_pdf.py
```

This will create a file under [jupyter-notebooks/data-for-eval/](./jupyter-notebooks/data_for_eval/)

[A sample is provided here](./jupyter-notebooks/data_for_eval/synthetic_tests_advanced_branching_50.csv)

### Step 3: Run the Indexing Pipeline

Execute the indexing script to process all data sources and store them in Elasticsearch:

```bash
cd jupyter-notebooks
uv run python scripts/rag/indexing.py
```

**Expected Output:**
```
Processing web URL: ['https://www.bbc.com/news/articles/c2l799gxjjpo', 'https://www.brookings.edu/articles/how-artificial-intelligence-is-transforming-the-world/']
Batches: 100%|███████████████████████████████████████████████████████████████████████████████████████████| 7/7 [00:01<00:00,  4.42it/s]
Indexing completed successfully!
```

Verify the ElasticSearch store was populated

```bash
curl -X GET "localhost:9200/_cat/health?v"
```

The pipeline will:
- Fetch and process web content from the Haystack blog
- Convert and chunk the PDF document into readable segments
- Generate 384-dimensional vector embeddings for all content

### Step 3: Verify Documents are Loaded

Check that documents have been successfully indexed:

```bash
# Get total document count
curl -X GET "localhost:9200/default/_count"

# Expected output: {"count":10,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0}}% 

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

### Step 4: Clean Up (Optional)

To stop the Elasticsearch container and clean up:

```bash
# Stop the container
docker-compose down

# Remove the index (if you want to start fresh)
curl -X DELETE "localhost:9200/default"
```

### Troubleshooting

**Issue: PDF not found warnings**
- Ensure you're running from the correct directory
- Verify the PDF file exists in `data_for_indexing/howpeopleuseai.pdf`



