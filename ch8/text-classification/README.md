# Text Classification with Haystack

This folder contains resources for learning how to build text classification pipelines using Haystack 2.0. These examples demonstrate various classification approaches, from zero-shot classification that requires no training data to sentiment analysis for business reviews, and web-based news categorization.

## Main Objective

The primary goal of these resources is to teach you how to:

1. **Implement Zero-Shot Classification**: Classify text into any categories without training data or model retraining
2. **Build Sentiment Analysis Pipelines**: Create end-to-end systems that fetch real-world data and analyze sentiment
3. **Integrate External APIs**: Connect Haystack pipelines with third-party services (Yelp, web search)
4. **Evaluate Classification Performance**: Use metrics, confusion matrices, and classification reports to assess model accuracy
5. **Create Custom Components**: Develop specialized components for data fetching, enrichment, and classification workflows
6. **Handle Multi-Category Classification**: Build systems that organize content across multiple predefined categories
## Use Cases

These text classification pipelines are valuable for:
- **Content Organization**: Automatically categorize news articles, documents, and web content
- **Sentiment Analysis**: Analyze customer reviews, social media posts, and feedback
- **Customer Support**: Route support tickets to appropriate teams based on content
- **Market Research**: Classify and analyze customer feedback by theme or sentiment
- **Content Moderation**: Automatically flag and categorize user-generated content
- **News Aggregation**: Organize articles by topic without manual tagging
- **Business Intelligence**: Analyze competitor reviews and market sentiment

---

## Contents

| Notebook | Link | Description |
|---|---|---|
| Zero-Shot Text Classification | [text-classification.ipynb](./text-classification.ipynb) | Comprehensive tutorial on zero-shot classification using pre-trained models, including dataset evaluation and performance metrics |
| Web-Based News Classification | [classification-with-haystack-search-pipeline.ipynb](./classification-with-haystack-search-pipeline.ipynb) | End-to-end pipeline that searches the web, fetches articles, and classifies them into categories (Politics, Sport, Technology, Entertainment, Business) |
| Sentiment Analysis Pipeline | [sentiment_analysis.ipynb](./sentiment_analysis.ipynb) | Advanced tutorial on building custom components for fetching Yelp reviews and performing sentiment analysis with transformer models |

### Supporting Files

| File | Description |
|---|---|
| [classification_model_used_df_file.csv](./classification_model_used_df_file.csv) | Dataset with 2,225 pre-labeled documents across 5 categories for evaluation |
| [df_file.csv](./df_file.csv) | Additional classification dataset |
| `images/` | Visualization assets including confusion matrices and pipeline diagrams |
| `haystack-agents-mini-project/` | Hands-on exercise combining classification and NER with agent-based orchestration |

---

### Folder challenge

The **haystack-agents-mini-project** folder contains a comprehensive hands-on exercise (~3 hours) that teaches you to build agent-orchestrated pipelines combining text classification and named entity recognition (NER). This mini-project is designed as a capstone exercise that brings together multiple concepts from the chapter.

**What You'll Build:**
- **EntityExtractor Component**: Custom NER component that extracts and filters entities (persons, organizations, locations) from text
- **Three Specialized Pipelines**: 
  - Classification pipeline (web search → classification)
  - NER extraction pipeline (web search → entity extraction)
  - Combined pipeline (web search → classification + entity extraction)
- **SuperComponents**: Simplified pipeline wrappers with clean interfaces for tool integration
- **Agent System**: Natural language agent that intelligently routes queries to the appropriate pipeline using tool calling
- **REST API Deployment**: Serialize pipelines and deploy via Hayhooks for production-ready endpoints

**Key Learning Outcomes:**
- Building custom components with complex logic
- Creating modular, reusable pipeline architectures
- Wrapping pipelines as agent tools
- Agent-based orchestration with natural language queries
- Pipeline serialization and deployment patterns
- Testing and debugging multi-component systems

The exercise includes a detailed Jupyter notebook ([classification-ner-agent-exercise.ipynb](./haystack-agents-mini-project/classification-ner-agent-exercise.ipynb)), comprehensive hints (HINTS.md), and a complete project structure with separate folders for classification and NER pipelines. This is an ideal project for practicing real-world pipeline development and deployment workflows.



## Pipeline Architectures

### 1. Zero-Shot Classification Pipeline
```
Load Dataset → TransformersZeroShotTextRouter → Predictions → Evaluation Metrics
```

**Key Features:**
- No training data required
- Instantly adaptable to new categories
- Model: `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`
- Evaluation against ground truth labels

### 2. Web-Based News Classification Pipeline
```
SearchApiWebSearch → LinkContentFetcher → HTMLToDocument → DocumentCleaner → NewsClassifier → Structured Output
```

**Key Features:**
- Real-time web content fetching
- Custom NewsClassifier component
- Automatic category assignment
- Metadata enrichment with labels

### 3. Sentiment Analysis Pipeline
```
YelpReviewFetcher → TransformersTextRouter → SentimentDocumentEnricher → Sentiment-Labeled Reviews
```

**Key Features:**
- Yelp API integration
- Sentiment model: `cardiffnlp/twitter-roberta-base-sentiment`
- Three-class sentiment (Positive, Negative, Neutral)
- Document metadata enrichment

---

## What You'll Learn

### 1. Zero-Shot Text Classification (`text-classification.ipynb`)
- Understanding zero-shot classification vs. traditional approaches
- Using pre-trained language models for classification
- Working with labeled datasets for evaluation
- Calculating accuracy, precision, recall, and F1 scores
- Interpreting confusion matrices
- Comparing model predictions against ground truth
- Best practices for category selection

### 2. Web-Based News Classification (`classification-with-haystack-search-pipeline.ipynb`)
- Building end-to-end web search + classification pipelines
- Integrating SearchAPI for web content discovery
- HTML content extraction and cleaning
- Creating custom classification components
- Chaining multiple processing steps
- Structuring classified output for analysis
- Real-time content categorization

### 3. Sentiment Analysis (`sentiment_analysis.ipynb`)
- Integrating external APIs (Yelp) into Haystack pipelines
- Building custom data fetcher components
- Implementing sentiment analysis with RoBERTa models
- Creating document enrichment components
- Handling API authentication securely
- Processing business reviews at scale
- Three-class sentiment classification
- Structuring sentiment results in metadata

---

## Key Concepts

### Zero-Shot Classification
Classification without training data for specific categories. The model uses its general language understanding to determine which label best fits the text. This approach is:
- **Flexible**: Change categories instantly without retraining
- **Fast**: No need to collect and label training data
- **Cost-Effective**: Eliminates expensive dataset preparation
- **Scalable**: Works across multiple domains and languages

### Sentiment Analysis
Determining the emotional tone of text (positive, negative, neutral). Applications include:
- Customer feedback analysis
- Brand reputation monitoring
- Product review analysis
- Social media sentiment tracking

### Custom Components
Extend Haystack with domain-specific functionality:
- **Data Fetchers**: Connect to external APIs and data sources
- **Enrichers**: Add metadata and analysis results to documents
- **Classifiers**: Implement specialized classification logic
- **Routers**: Direct documents based on classification results

### Pipeline Evaluation
Measure classification performance with:
- **Accuracy**: Overall correctness of predictions
- **Precision**: Accuracy of positive predictions
- **Recall**: Coverage of actual positive cases
- **F1 Score**: Harmonic mean of precision and recall
- **Confusion Matrix**: Visual breakdown of classification results

---

## Classification Categories

### News Categories (Web & Dataset Classification)
- **Politics**: Government, elections, policy, political figures
- **Sport**: Athletics, competitions, teams, sporting events
- **Technology**: Innovation, gadgets, software, tech companies
- **Entertainment**: Movies, music, celebrities, media
- **Business**: Companies, markets, economy, finance

### Sentiment Categories (Yelp Reviews)
- **Positive**: Favorable opinions, satisfaction, recommendations
- **Neutral**: Balanced or factual statements without strong emotion
- **Negative**: Criticism, dissatisfaction, complaints

---

## Example Use Cases

### News Aggregation Platform
Use the web-based classification pipeline to:
1. Search for articles on trending topics
2. Automatically categorize by subject
3. Organize content for different reader interests
4. Track coverage across categories

### Business Review Analysis
Use the sentiment analysis pipeline to:
1. Fetch reviews for your business or competitors
2. Classify sentiment automatically
3. Identify trends in customer satisfaction
4. Generate reports on positive vs. negative feedback

### Content Management System
Use zero-shot classification to:
1. Categorize incoming documents automatically
2. Route content to appropriate teams
3. Maintain organized content libraries
4. Enable category-based search and filtering

---

## Model Information

### Zero-Shot Classification Model
- **Model**: `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`
- **Architecture**: DeBERTa (Decoding-enhanced BERT with disentangled attention)
- **Capabilities**: Multi-label, multi-language classification
- **Strengths**: High accuracy, domain flexibility, no training required

### Sentiment Analysis Model
- **Model**: `cardiffnlp/twitter-roberta-base-sentiment`
- **Architecture**: RoBERTa (Robustly optimized BERT approach)
- **Training Data**: Twitter posts (short-form social media text)
- **Output Classes**: Negative (0), Neutral (1), Positive (2)
- **Strengths**: Fast inference, ideal for review-length text

---

## Getting Started

1. **Start with zero-shot classification** (`text-classification.ipynb`) to understand the fundamentals and see evaluation metrics
2. **Build a web classification system** (`classification-with-haystack-search-pipeline.ipynb`) to work with real-time content
3. **Implement sentiment analysis** (`sentiment_analysis.ipynb`) to learn API integration and custom component development

Each notebook builds on concepts from the previous ones while introducing new techniques and patterns.

---

## Chapter Topics Covered

1. **Zero-Shot Classification Fundamentals**
   - How zero-shot models work
   - When to use zero-shot vs. traditional classification
   - Category selection strategies
   
2. **Model Evaluation & Metrics**
   - Accuracy, precision, recall, F1 scores
   - Confusion matrix interpretation
   - Performance analysis across categories
   
3. **Haystack Pipeline Development**
   - Multi-component pipeline design
   - Web search and content fetching
   - Document processing and cleaning
   
4. **Custom Component Creation**
   - API integration patterns
   - Data fetching components
   - Document enrichment components
   - Classification wrapper components
   
5. **Production Text Classification Systems**
   - Building reliable classification pipelines
   - Handling diverse content types
   - Structuring outputs for downstream use
   - Real-time vs. batch processing patterns
   
6. **Sentiment Analysis**
   - Transformer-based sentiment classification
   - Business review analysis
   - Multi-class sentiment categorization
   - Metadata enrichment strategies
