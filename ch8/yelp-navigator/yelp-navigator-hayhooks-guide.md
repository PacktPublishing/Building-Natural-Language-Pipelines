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

## Pipeline Descriptions

### Pipeline 1: Business Search with NER
**Purpose**: Extract entities from natural language queries and search for businesses on Yelp.

**Components**:
- `QueryToDocument`: Converts query string to Haystack Document
- `NamedEntityExtractor`: Uses NER model to extract locations and keywords
- `EntityKeywordExtractor`: Processes entities into search parameters
- `YelpBusinessSearch`: Searches Yelp API with extracted parameters

**Input**: Natural language query (e.g., "best Mexican restaurants in Austin, Texas")

**Output**: JSON with business results including IDs, names, ratings, websites, locations

### Pipeline 2: Business Details Fetcher
**Purpose**: Fetch detailed business information and website content.

**Components**:
- `Pipeline1ResultParser`: Extracts business data from Pipeline 1 output
- `WebsiteURLExtractor`: Extracts website URLs and prepares metadata
- `LinkContentFetcher`: Fetches website content (Haystack component)
- `HTMLToDocument`: Converts HTML to Haystack Documents
- `DocumentCleaner`: Cleans and formats document content
- `DocumentMetadataEnricher`: Adds business metadata to documents

**Input**: Complete output from Pipeline 1

**Output**: Enriched Haystack Documents with website content and business metadata

### Pipeline 3: Reviews & Sentiment Analysis
**Purpose**: Fetch business reviews and perform sentiment analysis.

**Components**:
- `Pipeline1ResultParser`: Extracts business IDs from Pipeline 1 output
- `YelpReviewsFetcher`: Fetches reviews from Yelp API
- `BatchSentimentAnalyzer`: Analyzes sentiment using transformer models
- `ReviewsAggregatorByBusiness`: Aggregates reviews and identifies top/bottom reviews

**Input**: Complete output from Pipeline 1

**Output**: Aggregated documents per business with sentiment distribution and highlighted reviews

### Pipeline 4: Business Report Summarizer
**Purpose**: Generate comprehensive, AI-powered business reports from any combination of pipeline outputs.

**Components**:
- `FlexibleInputParser`: Consolidates data from Pipelines 1, 2, and/or 3
- `BusinessReportGenerator`: Uses OpenAI to generate professional business reports with:
  - Business overview
  - Offerings & services (if Pipeline 2 data available)
  - Customer feedback highlights (if Pipeline 3 data available)
  - Recommendation summary

**Input**: Flexible - accepts any combination of:
- `pipeline1_output`: Basic business information
- `pipeline2_output`: Website content and details (optional)
- `pipeline3_output`: Review analysis and sentiment (optional)

**Output**: Structured business reports with adaptive depth based on available inputs

**Report Sections**:
1. **Business Overview**: Location, pricing, establishment type
2. **Offerings & Services**: Key products/services (requires Pipeline 2)
3. **Customer Feedback Highlights**: Positive themes, areas of concern, overall sentiment (requires Pipeline 3)
4. **Recommendation Summary**: Target audience and considerations

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

## Usage Examples

### Basic Workflow (Single Business)

```bash
# Step 1: Search for businesses
curl -X POST http://localhost:1416/business_search/run \
  -H "Content-Type: application/json" \
  -d '{"query": "Italian restaurants in San Francisco"}' \
  > pipeline1_output.json

# Step 2: Generate basic report from search results
curl -X POST http://localhost:1416/business_summary_review/run \
  -H "Content-Type: application/json" \
  -d "$(jq -n --slurpfile p1 pipeline1_output.json '{pipeline1_output: $p1[0]}')"
```

### Enhanced Workflow (With Website Content)

```bash
# Steps 1-2: Get business details
curl -X POST http://localhost:1416/business_details/run \
  -H "Content-Type: application/json" \
  -d "$(jq -n --slurpfile p1 pipeline1_output.json '{pipeline1_output: $p1[0]}')" \
  > pipeline2_output.json

# Step 3: Generate enhanced report
curl -X POST http://localhost:1416/business_summary_review/run \
  -H "Content-Type: application/json" \
  -d "$(jq -n --slurpfile p1 pipeline1_output.json --slurpfile p2 pipeline2_output.json \
    '{pipeline1_output: $p1[0], pipeline2_output: $p2[0]}')"
```

### Complete Workflow (With Reviews & Sentiment)

```bash
# Steps 1-3: Get review analysis
curl -X POST http://localhost:1416/business_sentiment/run \
  -H "Content-Type: application/json" \
  -d "$(jq -n --slurpfile p1 pipeline1_output.json '{pipeline1_output: $p1[0]}')" \
  > pipeline3_output.json

# Step 4: Generate comprehensive report
curl -X POST http://localhost:1416/business_summary_review/run \
  -H "Content-Type: application/json" \
  -d "$(jq -n --slurpfile p1 pipeline1_output.json \
            --slurpfile p2 pipeline2_output.json \
            --slurpfile p3 pipeline3_output.json \
    '{pipeline1_output: $p1[0], pipeline2_output: $p2[0], pipeline3_output: $p3[0]}')"
```

---

## Next Steps

After building and deploying the pipelines:

1. **Test the API endpoints** using curl or the provided Jupyter notebook (`pipeline_chaining_guide.ipynb`)
2. **Experiment with Pipeline 4** at different report levels (basic, enhanced, complete)
3. **Integrate with LangGraph** for multi-agent orchestration
4. **Customize report templates** in `pipelines/business_summary_review/components.py`

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
