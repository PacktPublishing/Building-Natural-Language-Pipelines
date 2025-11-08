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
│   ├── business_sentiment/     # Pipeline 3: Reviews with Sentiment Analysis
│   │   ├── __init__.py
│   │   ├── components.py
│   │   ├── build_pipeline.py
│   │   └── pipeline_wrapper.py
│   └── business_summary_review/ # Pipeline 4: Business Report Summarizer
│       ├── __init__.py
│       ├── components.py
│       ├── build_pipeline.py
│       └── pipeline_wrapper.py
├── .env                        # Environment variables (API keys)
└── README.md                   # This file
```

## Prerequisites

### Environment Setup

Create a `.env` file in the `yelp-navigator` directory with your API keys:

```bash
# yelp-navigator/.env
RAPID_API_KEY=your_rapidapi_key_here
OPENAI_API_KEY=your_openai_key_here  # Only needed for Pipeline 1
```

### Build pipelines

Execute 

```bash
chmod +x build_all_pipelines.sh
./build_all_pipelines.sh
```

### Deploying with Hayhooks

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

**Pipeline 4 - Business Report Summarizer**:
- Endpoint: `http://localhost:1416/business_summary_review`
- Method: POST
- Body: Flexible - accepts any combination of pipeline outputs:
  - Basic: `{"pipeline1_output": {...}}`
  - With website: `{"pipeline1_output": {...}, "pipeline2_output": {...}}`
  - Complete: `{"pipeline1_output": {...}, "pipeline2_output": {...}, "pipeline3_output": {...}}`

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
└──────────────────┬──────────────────┘  │ - Identifies top/worst  │
                   │                      └───────────┬─────────────┘
                   │                                  │
                   └──────────────┬───────────────────┘
                                  ▼
                   ┌──────────────────────────────────┐
                   │ Pipeline 4: Report Generator     │
                   │ - Consolidates all information   │
                   │ - Generates comprehensive reports│
                   │ - Flexible depth based on inputs │
                   └──────────────────────────────────┘
```

### Pipeline 4 Report Levels

Pipeline 4 generates reports with different levels of detail based on available inputs:

- **Level 1 (Basic)**: Pipeline 1 only → Business overview with basic info
- **Level 2 (Enhanced)**: Pipelines 1+2 → Adds website content and offerings
- **Level 3 (Complete)**: Pipelines 1+2+3 → Full report with customer feedback and sentiment analysis

---

## Next Steps

After building and deploying the pipelines:

1. **Test the API endpoints** using curl or Postman
2. **Integrate with LangGraph** for multi-agent orchestration

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
