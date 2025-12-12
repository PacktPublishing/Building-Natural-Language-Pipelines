# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files first for better Docker layer caching
COPY pyproject.toml uv.lock ./

# Create .python-version file
RUN echo "3.11" > .python-version

# Create placeholder files that pyproject.toml references
RUN touch README.md LICENSE

# Copy source code (needed before uv sync for editable install)
COPY src/ ./src/

# Copy scripts
COPY scripts/ ./scripts/

# Copy data for indexing
COPY data_for_indexing/ ./data_for_indexing/

# Install dependencies using uv
ENV UV_SYSTEM_PYTHON=1
RUN uv sync --frozen --no-dev

# Make scripts executable
RUN chmod +x scripts/*.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Environment variables that must be provided at runtime:
# - OPENAI_API_KEY: OpenAI API key for embeddings and LLM
# - RAG_API_KEY: Secret key for securing the /query endpoint
# Example: docker run -e OPENAI_API_KEY=... -e RAG_API_KEY=... hybrid-rag-api

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Create startup script that runs indexing then starts API
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🔧 Running indexing pipeline..."\n\
uv run python -m src.rag.indexing\n\
echo "✅ Indexing complete!"\n\
echo "🚀 Starting API server..."\n\
exec uv run uvicorn src.app:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Default command - run indexing then start API
CMD ["/app/start.sh"]