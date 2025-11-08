# Yelp Navigator - Pipeline Setup Guide

This guide provides step-by-step instructions for building and serializing the Haystack pipelines used in the Yelp Navigator multi-agent architecture.

## Project Structure

```
yelp-navigator/
├── pipelines/
│   ├── business_search/        # Pipeline 1: Business Search with NER
│   │   ├── __init__.py
│   │   ├── components.py
│   │   ├── build_pipeline.py
│   │   └── pipeline_wrapper.py
│   ├── business_details/       # Pipeline 2: Business Details with Website Content
│   │   ├── __init__.py
│   │   ├── components.py
│   │   ├── build_pipeline.py
│   │   └── pipeline_wrapper.py
│   └── business_sentiment/     # Pipeline 3: Reviews with Sentiment Analysis
│       ├── __init__.py
│       ├── components.py
│       ├── build_pipeline.py
│       └── pipeline_wrapper.py
├── .env                        # Environment variables (API keys)
└── PIPELINE_SETUP.md          # This file
```

## Prerequisites

### Environment Setup

Create a `.env` file in the `yelp-navigator` directory with your API keys:

```bash
# yelp-navigator/.env
RAPID_API_KEY=your_rapidapi_key_here
OPENAI_API_KEY=your_openai_key_here  # Only needed for Pipeline 1
```

**Note**: All dependencies are managed at the `ch8` root level using `uv`. No need to install packages separately.

## Building and Serializing Pipelines

### Pipeline 1: Business Search with NER

**Purpose**: Extracts entities from natural language queries and searches Yelp for businesses.

**Location**: `pipelines/business_search/`

**How to Build**:

```bash
# Navigate to the business_search directory
cd pipelines/business_search

# Run the build script
python build_pipeline.py
```

**Output**: Creates `pipeline1_business_search_ner.yaml` in the `business_search` directory.

**What happens**:
- Loads NER model (`dslim/bert-base-NER`)
- Creates pipeline with components:
  - QueryToDocument
  - NamedEntityExtractor
  - EntityKeywordExtractor
  - YelpBusinessSearch
- Serializes to YAML for Hayhooks deployment

**Test the pipeline** (optional):
```python
from haystack import Pipeline
from dotenv import load_dotenv
import os

load_dotenv("../../.env")

# Load the serialized pipeline
with open("pipeline1_business_search_ner.yaml", "r") as f:
    pipeline = Pipeline.loads(f.read())

# Run a test query
result = pipeline.run(data={
    "query_converter": {"query": "cheese shops in Madison"}
})

print(result['yelp_search']['results'])
```

---

### Pipeline 2: Business Details with Website Content

**Purpose**: Fetches website content for businesses and creates enriched documents.

**Location**: `pipelines/business_details/`

**How to Build**:

```bash
# Navigate to the business_details directory
cd pipelines/business_details

# Run the build script
python build_pipeline.py
```

**Output**: Creates `pipeline2_business_details.yaml` in the `business_details` directory.

**What happens**:
- Creates pipeline with components:
  - Pipeline1ResultParser
  - WebsiteURLExtractor
  - LinkContentFetcher
  - HTMLToDocument
  - DocumentCleaner
  - DocumentMetadataEnricher
- Serializes to YAML for Hayhooks deployment

**Test the pipeline** (optional):
```python
from haystack import Pipeline

# Load the serialized pipeline
with open("pipeline2_business_details.yaml", "r") as f:
    pipeline = Pipeline.loads(f.read())

# Assuming you have pipeline1_output from Pipeline 1
result = pipeline.run(data={
    "parser": {"pipeline1_output": pipeline1_output}
})

print(f"Created {len(result['metadata_enricher']['documents'])} enriched documents")
```

---

### Pipeline 3: Reviews with Sentiment Analysis

**Purpose**: Fetches business reviews and performs sentiment analysis.

**Location**: `pipelines/business_sentiment/`

**How to Build**:

```bash
# Navigate to the business_sentiment directory
cd pipelines/business_sentiment

# Run the build script
python build_pipeline.py
```

**Output**: Creates `pipeline3_reviews_sentiment.yaml` in the `business_sentiment` directory.

**What happens**:
- Loads sentiment analysis model (`cardiffnlp/twitter-roberta-base-sentiment`)
- Creates pipeline with components:
  - Pipeline1ResultParser
  - YelpReviewsFetcher
  - BatchSentimentAnalyzer
  - ReviewsAggregatorByBusiness
- Serializes to YAML for Hayhooks deployment

**Note**: This pipeline takes longer to build as it downloads and loads the sentiment analysis transformer model.

**Test the pipeline** (optional):
```python
from haystack import Pipeline
from dotenv import load_dotenv

load_dotenv("../../.env")

# Load the serialized pipeline
with open("pipeline3_reviews_sentiment.yaml", "r") as f:
    pipeline = Pipeline.loads(f.read())

# Assuming you have pipeline1_output from Pipeline 1
result = pipeline.run(data={
    "parser": {"pipeline1_output": pipeline1_output}
})

documents = result['reviews_aggregator']['documents']
print(f"Analyzed reviews for {len(documents)} businesses")
```

---

## Building All Pipelines at Once

You can build all pipelines sequentially with this script:

```bash
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
```

Save this as `build_all_pipelines.sh` in the `yelp-navigator` directory and run:

```bash
chmod +x build_all_pipelines.sh
./build_all_pipelines.sh
```

---

## Deploying with Hayhooks

Once you've built and serialized the pipelines, you can deploy them with Hayhooks:

### Start Hayhooks Server

```bash
# From the yelp-navigator directory
hayhooks run --pipelines-dir pipelines
```

This will:
- Scan all subdirectories in `pipelines/`
- Load `pipeline_wrapper.py` from each directory
- Expose API endpoints for each pipeline

### Access the Pipelines

**Pipeline 1 - Business Search**:
- Endpoint: `http://localhost:1416/business_search`
- Method: POST
- Body: `{"query": "cheese shops in Madison"}`

**Pipeline 2 - Business Details**:
- Endpoint: `http://localhost:1416/business_details`
- Method: POST
- Body: `{"pipeline1_output": {...}}`

**Pipeline 3 - Reviews Sentiment**:
- Endpoint: `http://localhost:1416/business_sentiment`
- Method: POST
- Body: `{"pipeline1_output": {...}}`

---

## Troubleshooting

### Import Errors

If you encounter import errors when running the build scripts:

```bash
# Make sure you're running from the correct directory
cd yelp-navigator/pipelines/business_search  # or business_details, business_sentiment
python build_pipeline.py
```

### Missing API Keys

If you get authentication errors:

1. Check that `.env` file exists in `yelp-navigator/` directory
2. Verify `RAPID_API_KEY` is set correctly
3. Ensure the path to `.env` in build scripts is correct (`../../.env`)

### Model Download Issues

If transformer models fail to download:

1. Check your internet connection
2. Ensure you have sufficient disk space
3. Models are cached in `~/.cache/huggingface/`

### Pipeline Serialization Fails

If YAML serialization fails:

1. Ensure all custom components are properly decorated with `@component`
2. Check that all component connections are valid
3. Verify component output types match input types

---

## Pipeline Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ User Query: "cheese shops in Madison"                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Pipeline 1: Business Search with NER                           │
│ - Extracts entities (location, keywords)                       │
│ - Searches Yelp API                                            │
│ - Returns business results with IDs, names, websites, etc.     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ├──────────────────────┐
                           ▼                      ▼
┌─────────────────────────────────────┐  ┌─────────────────────────┐
│ Pipeline 2: Business Details        │  │ Pipeline 3: Reviews &   │
│ - Fetches website content           │  │   Sentiment Analysis    │
│ - Creates enriched documents        │  │ - Fetches reviews       │
│ - Returns docs with metadata        │  │ - Analyzes sentiment    │
└─────────────────────────────────────┘  │ - Identifies top/worst  │
                                         └─────────────────────────┘
```

---

## Next Steps

After building and deploying the pipelines:

1. **Test the API endpoints** using curl or Postman
2. **Integrate with LangGraph** for multi-agent orchestration
3. **Implement Pipeline 4** for summarization and recommendations
4. **Implement Pipeline 5** for interactive clarification with users

---

## Additional Resources

- **Haystack Documentation**: https://docs.haystack.deepset.ai/
- **Hayhooks Documentation**: https://docs.haystack.deepset.ai/docs/hayhooks
- **RapidAPI Yelp Business Reviews**: https://rapidapi.com/beat-analytics-beat-analytics-default/api/yelp-business-reviews

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review component implementations in `components.py` files
3. Verify pipeline connections in `build_pipeline.py` files
4. Test individual components before running full pipeline
