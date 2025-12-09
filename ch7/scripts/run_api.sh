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

# Check Qdrant storage
echo "🔍 Checking Qdrant storage..."
if [[ ! -d "./qdrant_storage" ]]; then
    echo "⚠️  Qdrant storage directory not found"
    echo "💡 Run indexing first: ./scripts/run_indexing.sh"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Qdrant storage directory exists"
fi

# Start the API
echo "🚀 Starting FastAPI application..."
echo "📡 API will be available at: http://localhost:8000"
echo "📖 API docs available at: http://localhost:8000/docs"
echo ""

uv run uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload