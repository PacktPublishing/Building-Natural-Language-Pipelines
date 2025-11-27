#!/bin/bash
# Quick start script for model testing

echo "🧪 Model Testing Quick Start"
echo "=============================="
echo ""

# Check if Ollama is running
echo "Checking Ollama status..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Please install Ollama first."
    exit 1
fi

# Check for required models
echo ""
echo "Checking required models..."
REQUIRED_MODELS=("gpt-oss:20b" "deepseek-r1:latest" "qwen3:latest")
MISSING_MODELS=()

for model in "${REQUIRED_MODELS[@]}"; do
    if ollama list | grep -q "$model"; then
        echo "  ✅ $model"
    else
        echo "  ❌ $model (missing)"
        MISSING_MODELS+=("$model")
    fi
done

# Offer to pull missing models
if [ ${#MISSING_MODELS[@]} -gt 0 ]; then
    echo ""
    echo "Missing models detected. These need to be pulled:"
    for model in "${MISSING_MODELS[@]}"; do
        echo "  - $model"
    done
    echo ""
    read -p "Pull missing models now? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for model in "${MISSING_MODELS[@]}"; do
            echo "Pulling $model..."
            ollama pull "$model"
        done
    else
        echo "Exiting. Please pull the models manually with:"
        for model in "${MISSING_MODELS[@]}"; do
            echo "  ollama pull $model"
        done
        exit 1
    fi
fi

echo ""
echo "=============================="
echo "Starting test suite..."
echo "=============================="
echo ""
echo "This will run 27 tests (3 models × 3 versions × 3 queries)"
echo "Estimated time: 10-30 minutes"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$(dirname "$0")"
    python test_models.py
else
    echo "Cancelled."
    exit 0
fi
