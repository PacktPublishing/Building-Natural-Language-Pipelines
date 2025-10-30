# Building RAG Applications with Haystack 2.0
Supplementary material for the book "Building Natural Language Pipelines" published by Packt

Author: Laura Funderburk

## What You'll Learn to Build

This book will guide you through building sophisticated **Retrieval-Augmented Generation (RAG) applications** using modern NLP techniques and the Haystack 2.0 framework. By the end of this journey, you'll have hands-on experience creating:

### 🔍 **Intelligent Search & Retrieval Systems**
- **Semantic search pipelines** that understand context and meaning, not just keywords
- **Hybrid search systems** combining traditional keyword search with vector-based semantic retrieval
- **Multi-modal document processing** pipelines for PDFs, web content, and structured data

### 🤖 **Advanced RAG Applications**
- **Question-answering systems** that can intelligently retrieve and synthesize information from large document collections
- **Conversational AI assistants** with memory and context awareness
- **Knowledge graph-enhanced RAG** systems that leverage structured relationships in data

### 🛠️ **Custom NLP Components**
- **Specialized text processors** for domain-specific content (legal, medical, technical documents)
- **Quality control components** with automated evaluation and validation
- **Synthetic data generators** for testing and augmenting your training datasets

### 🏗️ **Production-Ready Systems**
- **Scalable pipeline architectures** with proper error handling and monitoring
- **Dockerized applications** ready for cloud deployment
- **Evaluation frameworks** using RAGAS and other metrics for continuous improvement
- **API-based services** with FastAPI for serving your NLP models

### 🎯 **Real-World Projects**
- **Financial document analysis** system for processing earnings reports and market data
- **Legal document chatbot** for answering questions about contracts and regulations  
- **Named entity recognition** system for extracting structured information from unstructured text
- **Text classification** pipelines for content moderation and document categorization

Each chapter builds upon the previous one, taking you from NLP fundamentals to deploying production-grade applications that can handle real-world complexity and scale.

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

Set up a virtual environment and install the required packages:

### Set up - for Jupyter notebook usage

If you have completed the following, you may discard this information. Otherwise, as a reminder and to ease installation, you can follow the instructions below.  

Throughout this book we will be using `pip`, `conda` and `just` for package management. We will also create an isolated `conda` environment with Python 3.10.  

We recommend that you install Miniconda and VSCode. We also recommend that you install GitHub (GitBash for Windows or Git for Linux and Mac) to make the process of accessing the material locally easier.   

* Install Miniconda: https://docs.conda.io/projects/miniconda/en/latest/  

* Install VSCode: https://code.visualstudio.com/docs/setup/setup-overview  

To obtain the code and exercises, clone the repository: 

Open VSCode, Click File-> New Window, then Terminal ->New Terminal. Ensure your terminal is of type “Bash” or “Command line”.  

Within the terminal, type each of the commands (a command is identified by the $ sign) below, one by one. Then press enter.  

```bash

$ git clone https://github.com/PacktPublishing/Building-Natural-Language-Pipelines.git 

$ cd building-RAG-applications/ 

$ conda create –-name llm-pipelines python==3.12

$ conda activate llm-pipelines 

$ pip install haystack-ai, ipykernel, ipytthon
```

Enable the Jupyter Notebook extension on VSCode through the extension marketplace. When you open a notebook, press on ‘Select Kernel’ and click on `llm-pipeline` as our environment. 

### Advanced set up - for chapters 6 and higher

Please refer to the instructions in this [README](./ch6/README.md) for how to set up for advanced chapters



