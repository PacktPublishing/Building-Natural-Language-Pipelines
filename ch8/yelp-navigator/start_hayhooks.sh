#!/bin/bash
# Convenience script to start Hayhooks server with correct PYTHONPATH

cd "$(dirname "$0")"

# Load environment variables from .env file
if [ -f "../.env" ]; then
    echo "Loading environment variables from ../.env"
    export $(grep -v '^#' ../.env | xargs)
else
    echo "Warning: ../.env file not found"
fi

PYTHONPATH=$PWD:$PYTHONPATH uv run hayhooks run --pipelines-dir pipelines
