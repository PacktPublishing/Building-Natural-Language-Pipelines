#!/bin/bash
# Script to run the FastAPI application

set -euo pipefail

echo "🚀 Starting Hybrid RAG API..."

# Change to project root
cd "$(dirname "$0")/.."

# Load environment
if [[ -f .env ]]; then
    source .env
else
    echo "❌ .env file not found. Run ./scripts/setup_local.sh first"
    exit 1
fi

# Check Elasticsearch
echo "🔍 Checking Elasticsearch connection..."
if ! curl -f -s http://localhost:9200/_cat/health > /dev/null 2>&1; then
    echo "❌ Elasticsearch not available on localhost:9200"
    echo "💡 Start Elasticsearch first or use Docker: docker-compose up -d elasticsearch"
    exit 1
fi

echo "✅ Elasticsearch is running"

# Check if documents are indexed
echo "🔍 Checking if documents are indexed..."
doc_count=$(curl -s "http://localhost:9200/documents/_count" | python -c "import sys, json; print(json.load(sys.stdin)['count'])" 2>/dev/null || echo "0")

if [[ "$doc_count" == "0" ]]; then
    echo "⚠️  No documents found in Elasticsearch index 'documents'"
    echo "💡 Run indexing first: ./scripts/run_indexing.sh"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Found $doc_count documents in index"
fi

# Start the API
echo "🚀 Starting FastAPI application..."
echo "📡 API will be available at: http://localhost:8000"
echo "📖 API docs available at: http://localhost:8000/docs"
echo ""

uv run uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload