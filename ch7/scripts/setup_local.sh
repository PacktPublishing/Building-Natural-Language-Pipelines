#!/bin/bash
# Setup script for local development

set -euo pipefail

echo "🚀 Setting up Hybrid RAG local development environment..."

# Change to project root
cd "$(dirname "$0")/.."

# Check if .env exists
if [[ ! -f .env ]]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your OPENAI_API_KEY"
else
    echo "✅ .env file already exists"
fi

# Install dependencies using uv
echo "📦 Installing dependencies with uv..."
uv sync

# Check if Elasticsearch is running
echo "🔍 Checking Elasticsearch..."
if curl -f -s http://localhost:9200/_cat/health > /dev/null 2>&1; then
    echo "✅ Elasticsearch is running on localhost:9200"
else
    echo "❌ Elasticsearch not found on localhost:9200"
    echo "💡 Start Elasticsearch with: docker run -d -p 9200:9200 -e discovery.type=single-node -e xpack.security.enabled=false docker.elastic.co/elasticsearch/elasticsearch:8.11.1"
fi

# Test OpenAI API key
echo "🔑 Testing OpenAI API key..."
if uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env')
api_key = os.getenv('OPENAI_API_KEY')
if not api_key or api_key == 'your_openai_api_key_here':
    print('❌ OPENAI_API_KEY not set or using placeholder')
    exit(1)
else:
    print('✅ OPENAI_API_KEY found')
"; then
    echo "✅ OpenAI API key configured"
else
    echo "❌ OpenAI API key not configured"
    echo "💡 Please set OPENAI_API_KEY in .env file"
fi

echo ""
echo "🎉 Setup complete! Next steps:"
echo "  1. Edit .env file and set your OPENAI_API_KEY"
echo "  2. Start Elasticsearch (if not running)"
echo "  3. Run indexing: ./scripts/run_indexing.sh"
echo "  4. Start API: ./scripts/run_api.sh"
echo "  5. Test API: uv run python tests/test_api.py"