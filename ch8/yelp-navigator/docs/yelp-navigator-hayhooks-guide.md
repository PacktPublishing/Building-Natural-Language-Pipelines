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
├── .env                        # Environment variables (API keys)
└── README.md                   # This file
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

From the `yelp-navigator` directory:

```bash
sh start_hayhooks.sh
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
                   │                                  │ 
                   ▼                                  ▼
```


## Usage Examples

### Basic Workflow (Single Business)

```bash
# Step 1: Search for businesses
curl -X POST http://localhost:1416/business_search/run \
  -H "Content-Type: application/json" \
  -d '{"query": "Italian restaurants in San Francisco"}' \
  > pipeline1_output.json
```

### Enhanced Workflow (With Website Content)

```bash
# Step 2: Get business details
curl -X POST http://localhost:1416/business_details/run \
  -H "Content-Type: application/json" \
  -d "$(jq -n --slurpfile p1 pipeline1_output.json '{pipeline1_output: $p1[0]}')" \
  > pipeline2_output.json
```

### Complete Workflow (With Reviews & Sentiment)

```bash
# Step 3: Get review analysis
curl -X POST http://localhost:1416/business_sentiment/run \
  -H "Content-Type: application/json" \
  -d "$(jq -n --slurpfile p1 pipeline1_output.json '{pipeline1_output: $p1[0]}')" \
  > pipeline3_output.json
```

---

## Next Steps

After building and deploying the pipelines:

1. **Test the API endpoints** using curl or the provided Jupyter notebook (`pipeline_chaining_guide.ipynb`)
2. **Integrate with LangGraph** for multi-agent orchestration
3. **Customize components** in the respective `pipelines/*/components.py` files

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
