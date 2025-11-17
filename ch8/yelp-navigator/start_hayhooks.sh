#!/bin/bash
# Convenience script to start Hayhooks server with correct PYTHONPATH

cd "$(dirname "$0")"
PYTHONPATH=$PWD:$PYTHONPATH uv run hayhooks run --pipelines-dir pipelines
