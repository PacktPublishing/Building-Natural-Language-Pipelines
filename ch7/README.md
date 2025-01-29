# Description

Exercises for Chapter 7. "Deploying Haystack-based applications"

## Topics covered

* Transition from exploratory development to deployment-focused engineering. 
* Leverage APIs to serve results and create user-facing interfaces. 
* Develop custom API endpoints tailored to your application's unique requirements. 
* Structure and package your pipeline for smooth, automated deployment using Docker and CI/CD practices. 

## Material

### Method 1: Build a custom endpoint with FastAPI, Bytewax and Docker

1. [Indexing dataflow](./api-dockerization/indexing_dataflow.py) - This script combines a Haystack indexing pipeline with custom components with a Bytewax dataflow to enable filtering data with a streaming approach.
2. [Querying pipeline](./api-dockerization/querying.py) - This script contains a retriever pipeline to answer queries in natural language.
3. [API with FastAPI](./api-dockerization/app.py) - This is a sample implementation of an API with an endpoint taking as input a stock symbol and a question in natural language.
4. [Sample Dockerfile](./api-dockerization/Dockerfile) - This is a simple file to dockerize the API. 

### Method 2: Use pipeline serialization and Hayhooks to deploy a pipeline endpoint

1. [Sample pipeline with a prompt template](./pipeline-serialization/sample_pipeline.py)
2. [Serialized pipeline](./pipeline-serialization/chat_pipeline.yaml)
