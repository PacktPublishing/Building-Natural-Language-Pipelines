# Text Classification with Haystack

Learn to build text classification pipelines using Haystack 2.0, from zero-shot classification to sentiment analysis and web-based news categorization.

## What You'll Learn

- **Zero-Shot Classification**: Classify text without training data or model retraining
- **Sentiment Analysis**: Build end-to-end pipelines that fetch and analyze real-world data
- **API Integration**: Connect Haystack with external services (Yelp, web search)
- **Performance Evaluation**: Use metrics and confusion matrices to assess accuracy
- **Custom Components**: Create specialized components for data fetching and classification
- **Agent Orchestration**: Build intelligent systems that route queries to specialized pipelines

---

## Notebooks & Exercises

### Core Tutorials

1. **[text-classification.ipynb](./text-classification.ipynb)** - Zero-Shot Classification
   - Learn classification without training data
   - Work with pre-trained models (DeBERTa)
   - Evaluate with metrics and confusion matrices

2. **[classification-with-haystack-search-pipeline.ipynb](./classification-with-haystack-search-pipeline.ipynb)** - Web-Based Classification
   - Build end-to-end web search → classification pipeline
   - Classify news articles (Politics, Sport, Technology, Entertainment, Business)
   - Create custom classification components

3. **[sentiment_analysis.ipynb](./sentiment_analysis.ipynb)** - Sentiment Analysis
   - Integrate Yelp API for review fetching
   - Build custom data fetcher components
   - Perform three-class sentiment analysis (Positive, Neutral, Negative)

### Hands-On Challenge

4. **[haystack-agents-mini-project/](./haystack-agents-mini-project/)** - Agent-Orchestrated Pipelines
   
   Capstone exercise combining classification and NER with agent-based orchestration:
   - Build custom EntityExtractor component for NER
   - Create three specialized pipelines (classification, NER, combined)
   - Wrap pipelines as SuperComponents for tool integration
   - Develop natural language agent with intelligent query routing
   - Deploy via Hayhooks REST API
   
   Includes: [exercise notebook](./haystack-agents-mini-project/classification-ner-agent-exercise.ipynb), hints, and complete project structure.



## Pipeline Architectures

**Zero-Shot Classification**
```
Load Dataset → TransformersZeroShotTextRouter → Predictions → Evaluation
```
Model: `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`

**Web-Based News Classification**
```
SearchApiWebSearch → LinkContentFetcher → HTMLToDocument → DocumentCleaner → NewsClassifier
```
Categories: Politics, Sport, Technology, Entertainment, Business

**Sentiment Analysis**
```
YelpReviewFetcher → TransformersTextRouter → SentimentDocumentEnricher
```
Model: `cardiffnlp/twitter-roberta-base-sentiment` (3-class: Positive, Neutral, Negative)

---

## Key Concepts

**Zero-Shot Classification**  
Classify text without training data. The model uses its language understanding to match text to labels instantly. Benefits: flexible, fast, no dataset preparation needed.

**Custom Components**  
Extend Haystack with specialized functionality:
- **Data Fetchers** - Connect to external APIs (Yelp, web search)
- **Enrichers** - Add metadata and analysis results
- **Classifiers** - Implement domain-specific logic
- **Routers** - Direct documents based on classification

**Evaluation Metrics**  
- **Accuracy** - Overall correctness
- **Precision** - Accuracy of positive predictions
- **Recall** - Coverage of actual positives
- **F1 Score** - Harmonic mean of precision and recall
- **Confusion Matrix** - Visual performance breakdown

---

## Getting Started

**Recommended Path:**
1. Start with `text-classification.ipynb` - Learn fundamentals and evaluation metrics
2. Progress to `classification-with-haystack-search-pipeline.ipynb` - Build real-time web pipelines
3. Continue with `sentiment_analysis.ipynb` - Master API integration and custom components
4. Complete `haystack-agents-mini-project/` - Apply everything in an agent-orchestrated system

---

## Use Cases

- **Content Organization** - Categorize news, documents, web content automatically
- **Sentiment Analysis** - Analyze customer reviews and social media feedback
- **Customer Support** - Route tickets based on content classification
- **Market Research** - Analyze customer feedback by theme and sentiment
- **News Aggregation** - Organize articles by topic without manual tagging
- **Business Intelligence** - Track competitor reviews and market sentiment
