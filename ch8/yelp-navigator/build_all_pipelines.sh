#!/bin/bash
# build_all_pipelines.sh

echo "Building Pipeline 1: Business Search with NER..."
cd pipelines/business_search
python build_pipeline.py
cd ../..

echo ""
echo "Building Pipeline 2: Business Details with Website Content..."
cd pipelines/business_details
python build_pipeline.py
cd ../..

echo ""
echo "Building Pipeline 3: Reviews with Sentiment Analysis..."
cd pipelines/business_sentiment
python build_pipeline.py
cd ../..

echo ""
echo "✓ All pipelines built successfully!"