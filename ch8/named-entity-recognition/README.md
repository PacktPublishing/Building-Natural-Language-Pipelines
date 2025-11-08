# Named Entity Recognition with Haystack

This folder contains resources for learning how to build Named Entity Recognition (NER) pipelines using Haystack 2.0. These examples demonstrate how to automatically extract and categorize named entities (people, organizations, locations, and miscellaneous entities) from web content.

## Main Objective

The primary goal of these resources is to teach you how to:

1. **Build End-to-End NER Pipelines**: Create complete workflows that search the web, fetch content, and extract structured entity information
2. **Integrate Pre-trained NER Models**: Use state-of-the-art NER models within Haystack pipelines
3. **Create Custom Processing Components**: Develop specialized components for filtering, deduplicating, and structuring entity data
4. **Handle Web Content**: Extract and process real-world content from web searches and HTML pages
5. **Structure Extracted Data**: Transform unstructured text into organized, analyzable entity datasets

## Use Cases

These NER pipelines are valuable for:
- **Media Monitoring**: Track mentions of people, organizations, and places in news articles
- **Research & Analysis**: Gather and categorize information about specific topics or entities
- **Content Tagging**: Automatically tag and organize web content by identified entities
- **Knowledge Base Creation**: Extract structured information from unstructured web data
- **Competitive Intelligence**: Monitor mentions of companies, products, and key individuals

---

## Contents

| Resource | Link | Description |
|---|---|---|
| Interactive NER Pipeline Notebook | [ner-with-haystack-search-pipeline.ipynb](./ner-with-haystack-search-pipeline.ipynb) | Complete tutorial notebook demonstrating web search + NER pipeline with detailed explanations and custom components |
| Production NER Script | [ner-from-web.py](./ner-from-web.py) | Production-ready Python script for running NER extraction from web search results |
| Sample Output | [ner_output.csv](./ner_output.csv) | Example output file showing structured entity extraction results |

---

## Pipeline Architecture

The NER pipeline follows this modular flow:

```
SearchApiWebSearch → LinkContentFetcher → HTMLToDocument → DocumentCleaner → NamedEntityExtractor → NERPopulator → Structured Output
```

### Components Explained:

1. **SearchApiWebSearch**: Searches the web for relevant articles based on your query
2. **LinkContentFetcher**: Downloads content from search result URLs
3. **HTMLToDocument**: Converts HTML content into Haystack Document objects
4. **DocumentCleaner**: Removes extra whitespace, empty lines, and unwanted formatting
5. **NamedEntityExtractor**: Uses ML models to identify named entities in text
6. **NERPopulator** (Custom): Filters entities by confidence, removes duplicates, and structures results into categories:
   - **PER**: Person names (e.g., "Elon Musk", "Jeff Bezos")
   - **ORG**: Organizations (e.g., "Tesla", "SpaceX", "NASA")
   - **LOC**: Locations (e.g., "California", "United States", "Mars")
   - **MISC**: Miscellaneous entities (e.g., events, products, concepts)

---

## What You'll Learn

### 1. Interactive Notebook (`ner-with-haystack-search-pipeline.ipynb`)
- Complete step-by-step tutorial with explanations
- How to configure and connect Haystack components
- Creating custom components for specialized processing
- Entity filtering and deduplication strategies
- Visualizing and analyzing extracted entities
- Best practices for production NER pipelines

### 2. Production Script (`ner-from-web.py`)
- Ready-to-use implementation for automated entity extraction
- Command-line execution for batch processing
- CSV output generation for data analysis
- Error handling and resilience patterns

---

## Key Features

### Entity Confidence Filtering
The pipeline filters entities based on confidence scores to ensure high-quality results, reducing false positives.

### Duplicate Removal
Automatically deduplicates entities within each category to provide clean, unique entity lists per document.

### Source Tracking
Maintains URL references for each extracted entity set, enabling traceability back to original sources.

### Flexible Output
Results can be accessed programmatically or exported to CSV for analysis in spreadsheet tools, databases, or visualization platforms.

---

## Example Output Structure

Each processed document produces structured entity data:

```python
{
    "url": "https://example.com/article",
    "entities": {
        "PER": ["Elon Musk", "Tim Cook"],
        "ORG": ["Tesla", "Apple", "NASA"],
        "LOC": ["California", "Palo Alto"],
        "MISC": ["Model S", "iPhone 15"]
    }
}
```

---

## Getting Started

1. **Start with the notebook** (`ner-with-haystack-search-pipeline.ipynb`) to understand the concepts and see interactive results
2. **Run the production script** (`ner-from-web.py`) for automated entity extraction workflows
3. **Examine the sample output** (`ner_output.csv`) to understand the data structure

---

## Chapter Topics Covered

1. **Named Entity Recognition Fundamentals**
   - Understanding entity types (PER, ORG, LOC, MISC)
   - Confidence scoring and quality control
   
2. **Haystack Pipeline Development**
   - Web search integration
   - Content fetching and HTML processing
   - Document cleaning and preprocessing
   
3. **Custom Component Creation**
   - Designing specialized processing components
   - Implementing filtering and deduplication logic
   - Structuring outputs for downstream use
   
4. **Production NER Systems**
   - Building reliable extraction pipelines
   - Handling real-world web content
   - Exporting structured data for analysis
