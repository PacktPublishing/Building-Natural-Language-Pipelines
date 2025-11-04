#!/bin/bash
# Script to run document indexing

set -euo pipefail

echo "📚 Running document indexing pipeline..."

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

# Run indexing
echo "🚀 Starting indexing pipeline..."
uv run python -m src.rag.indexing

echo "✅ Indexing complete!"