#!/bin/bash
# build_all_pipelines.sh

echo "Building Pipeline 1: Classification..."
cd pipelines/classification
python build_pipeline.py
cd ../..

echo ""
echo "Building Pipeline 2: NER..."
cd pipelines/ner_extraction
python build_pipeline.py
cd ../..

