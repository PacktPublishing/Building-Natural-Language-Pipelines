# Building RAG Applications with Haystack 2.0
Supplementary material for the book "Building Natural Language Pipelines" published by Packt

Author: Laura Funderburk

## What You'll Learn to Build

This book guides you through building advanced **Retrieval-Augmented Generation (RAG)** with evaluation using the [Haystack 2.0](https://haystack.deepset.ai/) framework. Starting with NLP fundamentals, you'll progress through creating intelligent search systems, custom components, and production-ready applications. The journey culminates in deploying scalable RAG solutions with proper evaluation frameworks, containerized deployments, and real-world projects including financial document analysis, legal chatbots, and text classification systems.

## Key Techniques by Chapter

### **Chapter 3: Introduction to Haystack**
**Core Concepts & Foundation**
- **Component Architecture**: Understanding Haystack's modular design patterns
- **Pipeline Construction**: Building linear and branching data flow pipelines  
- **Document Processing**: Text extraction, cleaning, and preprocessing workflows
- **Basic Retrievers**: Implementing BM25 and TF-IDF keyword-based search
- **Generator Integration**: Connecting retrieval with text generation models
- **Error Handling**: Pipeline debugging and component validation techniques

### **Chapter 4: Advanced Pipeline Patterns**
**Scaling & Optimization**
- **Vector Embeddings**: Semantic search using sentence transformers and embedding models
- **Hybrid Retrieval**: Combining keyword (BM25) and semantic (vector) search strategies
- **Document Stores**: Working with Elasticsearch, FAISS, and Weaviate for scalable storage
- **Indexing Pipelines**: Automated document ingestion and preprocessing workflows
- **Query Expansion**: Advanced retrieval techniques using query reformulation
- **Pipeline Composition**: Building complex, multi-stage RAG architectures
- **Performance Optimization**: Caching, batching, and parallel processing strategies

### **Chapter 5: Custom Component Development**
**Extensibility & Testing**
- **Component SDK**: Creating custom Haystack components with proper interfaces
- **Knowledge Graph Integration**: Building components for structured knowledge representation
- **Synthetic Data Generation**: Automated test data creation for pipeline validation
- **Quality Control Systems**: Implementing automated evaluation and monitoring components
- **Unit Testing Frameworks**: Comprehensive testing strategies for NLP components
- **Component Lifecycle**: Initialization, serialization, and state management
- **Advanced Transformations**: Custom document processors for domain-specific content



## Chapter breakdown

* [ch1](./ch1/) - "Introduction to Natural Language Processing (NLP) pipelines"
* [ch2](./ch2/) - "Diving deep into Large Language Models (LLMs)"
* [ch3](./ch3/) - "Introduction to Haystack by deepset"
* [ch4](./ch4/) - "Bringing components together: Haystack pipelines for different use cases"
* [ch5](./ch5/) - "Haystack pipeline development with custom components"
* [ch6](./ch6/) - "Setting up a reproducible project: question and answer pipeline"
* [ch7](./ch7/) - "Deploying Haystack-based applications"
* [ch8](./ch8/) - "Hands-on projects"

## Setting up

Clone the repository

```bash
git clone https://github.com/PacktPublishing/Building-Natural-Language-Pipelines.git

cd Building-Natural-Language-Pipelines/

```