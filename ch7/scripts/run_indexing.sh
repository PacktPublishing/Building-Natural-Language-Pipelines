#!/bin/bash
# Script to run document indexing with Qdrant

set -euo pipefail

echo "📚 Running document indexing pipeline with Qdrant..."

# Change to project root
cd "$(dirname "$0")/.."

# Load environment
if [[ -f .env ]]; then
    source .env
else
    echo "❌ .env file not found. Run ./scripts/setup_local.sh first"
    exit 1
fi

# Create Qdrant storage directory if it doesn't exist
QDRANT_PATH="${QDRANT_PATH:-./qdrant_storage}"
if [[ ! -d "$QDRANT_PATH" ]]; then
    echo "📁 Creating Qdrant storage directory: $QDRANT_PATH"
    mkdir -p "$QDRANT_PATH"
fi

echo "✅ Using Qdrant storage at: $QDRANT_PATH"

# Run indexing
echo "🚀 Starting indexing pipeline..."
uv run python -m src.rag.indexing

echo "✅ Indexing complete!"