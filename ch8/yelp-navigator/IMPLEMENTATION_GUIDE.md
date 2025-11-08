# Yelp Navigator - Pipeline Implementation Guide

## Overview
This folder contains 5 Jupyter notebooks implementing a complete multi-agent architecture for searching, analyzing, and recommending Yelp businesses based on natural language queries.

## Pipelines

### 📍 Pipeline 1: Business Search with NER
**File**: `pipeline1_business_search_ner.ipynb`

**Purpose**: Extract entities from natural language queries and search for businesses on Yelp

**Components**:
- QueryToDocument: Converts query to Haystack Document
- NamedEntityExtractor: Extracts locations and keywords using NER
- EntityKeywordExtractor: Processes entities into search parameters
- YelpBusinessSearch: Searches Yelp API

**Input**: Natural language query (e.g., "best Mexican restaurants in Madison, WI")

**Output**: 
- JSON results with business information
- Business IDs and aliases for downstream pipelines
- Search parameters used

**Example Usage**:
```python
result = pipeline.run(data={"query_converter": {"query": "cheese curds in Madison, WI"}})
api_results = result['yelp_search']['results']
business_ids = extract_business_info(api_results)
```

---

### 📋 Pipeline 2: Business Details Fetcher
**File**: `pipeline2_business_details.ipynb`

**Purpose**: Fetch detailed business information and website content

**Components**:
- YelpBusinessDetailsFetcher: Gets business details from API
- WebsiteURLExtractor: Extracts website URLs and metadata
- LinkContentFetcher: Fetches website content
- HTMLToDocument: Converts HTML to Haystack Documents
- DocumentMetadataEnricher: Adds business metadata to documents

**Input**: Business IDs and aliases from Pipeline 1

**Output**: 
- Enriched Haystack Documents with:
  - Price range, rating, location coordinates
  - Website content
  - Contact information

**Example Usage**:
```python
result = pipeline.run(data={
    "details_fetcher": {
        "business_ids": ["id1", "id2"],
        "business_aliases": ["alias1", "alias2"]
    }
})
documents = result['metadata_enricher']['documents']
```

---

### ⭐ Pipeline 3: Reviews with Sentiment Analysis
**File**: `pipeline3_reviews_sentiment.ipynb`

**Purpose**: Fetch business reviews and perform sentiment analysis

**Components**:
- YelpReviewsFetcher: Fetches reviews from Yelp API
- BatchSentimentAnalyzer: Analyzes sentiment using transformer models
- ReviewsAggregatorByBusiness: Aggregates and identifies top/bottom reviews

**Input**: Business IDs from Pipeline 1

**Output**: 
- Aggregated documents per business with:
  - Sentiment distribution (positive/neutral/negative counts)
  - Highest-rated reviews with positive sentiment
  - Lowest-rated reviews with negative sentiment
  - Full review metadata

**Example Usage**:
```python
result = pipeline.run(data={
    "reviews_fetcher": {
        "business_ids": ["id1", "id2"]
    }
})
documents = result['reviews_aggregator']['documents']
insights = extract_review_insights(documents)
```

---

### 💡 Pipeline 4: Summary and Recommendations
**File**: `pipeline4_summary_recommendations.ipynb`

**Purpose**: Generate summaries, identify themes, and provide recommendations

**Components**:
- ReviewThemeExtractor: Extracts themes from review documents
- ThemeSummaryGenerator: Uses LLM to generate theme summaries
- RecommendationEngine: Creates personalized recommendations

**Input**: 
- Aggregated review documents from Pipeline 3
- User request/preferences

**Output**: 
- Personalized recommendations with:
  - Theme analysis (positive and negative)
  - Recommendation (Yes/No with reasoning)
  - Best suited for...
  - Caveats and concerns

**Example Usage**:
```python
result = pipeline.run(data={
    "theme_extractor": {"documents": review_documents},
    "recommendation_engine": {"user_request": "I want authentic Mexican food"}
})
recommendations = result['recommendation_engine']['recommendations']
```

---

### 🗣️ Pipeline 5: Interactive User Clarification
**File**: `pipeline5_interactive_clarification.ipynb`

**Purpose**: Interactive conversation to extract location and keywords from vague queries

**Components**:
- ClarifyingQuestionGenerator: Generates targeted questions
- InformationExtractor: Extracts location and keywords from responses
- InteractiveConversationManager: Orchestrates conversation flow

**Input**: Vague or incomplete user queries

**Output**: 
- Extracted location
- Extracted keywords
- Ready status (when enough information collected)

**Example Usage**:
```python
manager = InteractiveConversationManager(api_key=OPENAI_API_KEY)
response = manager.start_conversation("I want food")
# Continue conversation...
params = manager.get_search_parameters()
query = f"{' '.join(params['keywords'])} in {params['location']}"
```

---

## Complete Workflow

### End-to-End Example

```python
# Step 1: Interactive Clarification (Pipeline 5)
manager = InteractiveConversationManager(api_key=OPENAI_API_KEY)
# ... conversation to extract location and keywords ...
params = manager.get_search_parameters()
query = f"{' '.join(params['keywords'])} in {params['location']}"

# Step 2: Search for Businesses (Pipeline 1)
result1 = pipeline1.run(data={"query_converter": {"query": query}})
business_info = extract_business_info(result1['yelp_search']['results'])

# Step 3: Get Business Details (Pipeline 2) - Optional
result2 = pipeline2.run(data={
    "details_fetcher": {
        "business_ids": business_info['business_ids'],
        "business_aliases": business_info['business_aliases']
    }
})

# Step 4: Analyze Reviews (Pipeline 3)
result3 = pipeline3.run(data={
    "reviews_fetcher": {"business_ids": business_info['business_ids']}
})

# Step 5: Get Recommendations (Pipeline 4)
result4 = pipeline4.run(data={
    "theme_extractor": {"documents": result3['reviews_aggregator']['documents']},
    "recommendation_engine": {"user_request": params['user_request']}
})

# Display recommendations
recommendations = result4['recommendation_engine']['recommendations']
print(format_recommendations(recommendations))
```

---

## Architecture Diagram

```
User Input (vague query)
        ↓
[Pipeline 5: Interactive Clarification]
        ├─→ Extract Location
        └─→ Extract Keywords
        ↓
[Pipeline 1: Business Search with NER]
        └─→ Business IDs & Aliases
        ↓
[Pipeline 2: Business Details] ←─┐
        └─→ Enriched Documents    │ (Optional)
        ↓                          │
[Pipeline 3: Reviews & Sentiment] │
        └─→ Analyzed Reviews       │
        ↓                          │
[Pipeline 4: Recommendations] ←───┘
        └─→ Final Recommendations
```

---

## Setup Requirements

### Environment Variables
Create a `.env` file in the project root with:
```
RAPID_API_KEY=your_rapidapi_key_here
OPENAI_API_KEY=your_openai_key_here
```

### API Keys Required
1. **RapidAPI Key**: Subscribe to Yelp Business Reviews API at https://rapidapi.com/beat-analytics-beat-analytics-default/api/yelp-business-reviews
2. **OpenAI API Key**: Get from https://platform.openai.com/api-keys

### Dependencies
```bash
pip install haystack-ai
pip install requests
pip install python-dotenv
pip install transformers
pip install torch
```

---

## Pipeline Data Flow

### Data Formats

**Pipeline 1 Output**:
```python
{
    "results": {
        "resultCount": 240,
        "results": [
            {
                "bizId": "RJNAeNA-209sctUO0dmwuA",
                "name": "The Old Fashioned",
                "alias": "the-old-fashioned-madison",
                "rating": 4.1,
                "categories": ["American", "Beer Bars"],
                "priceRange": "$$",
                ...
            }
        ]
    }
}
```

**Pipeline 2 Output**:
```python
Document(
    content="<website HTML content>",
    meta={
        "business_id": "RJNAeNA-209sctUO0dmwuA",
        "business_name": "The Old Fashioned",
        "price_range": "$$",
        "latitude": 43.07618625,
        "longitude": -89.38375722,
        "rating": 4.1,
        "website": "http://theoldfashioned.com/",
        ...
    }
)
```

**Pipeline 3 Output**:
```python
Document(
    content="<summary of reviews>",
    meta={
        "business_id": "RJNAeNA-209sctUO0dmwuA",
        "total_reviews": 10,
        "positive_count": 7,
        "negative_count": 1,
        "highest_rated_reviews": [...],
        "lowest_rated_reviews": [...],
        ...
    }
)
```

**Pipeline 4 Output**:
```python
{
    "business_id": "RJNAeNA-209sctUO0dmwuA",
    "sentiment_score": 0.7,
    "theme_analysis": "Key Positive Themes: ...",
    "recommendation": "Recommendation: Yes (High Confidence)...",
    ...
}
```

---

## Use Cases

1. **Restaurant Discovery**: Help users find restaurants matching specific criteria
2. **Sentiment Analysis**: Understand customer sentiment about businesses
3. **Review Summarization**: Quickly digest key themes from many reviews
4. **Personalized Recommendations**: Match businesses to user preferences
5. **Interactive Search**: Handle vague queries through conversation

---

## Notes

- **In-Memory Processing**: All pipelines use in-memory document processing (no persistent document store)
- **API Rate Limits**: RapidAPI free tier has rate limits; consider this when testing
- **Model Loading**: NER and sentiment models download on first run (~500MB total)
- **Response Times**: LLM calls (Pipeline 4, 5) may take 5-10 seconds per request

---

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure `.env` file is in the correct location and contains valid keys
2. **Model Download Failures**: Check internet connection; models download from HuggingFace
3. **Rate Limit Errors**: Wait or upgrade RapidAPI plan
4. **Memory Issues**: Sentiment analysis requires ~2GB RAM for models

### Debug Tips

- Run notebooks cell by cell to isolate issues
- Check API responses for error messages
- Verify business IDs are valid when testing Pipeline 2-4
- Use smaller `max_reviews_per_business` in Pipeline 3 for faster testing

---

## Future Enhancements

- Add persistent document store (Elasticsearch, Qdrant)
- Implement caching for API responses
- Create unified LangGraph agent orchestrating all pipelines
- Add more sophisticated NER for cuisine types and food preferences
- Implement result ranking based on multiple factors
- Add support for business comparisons

---

## Contact & Support

For issues or questions, refer to the main project README or the Yelp Business Reviews API documentation.
