import wandb
from haystack import Pipeline
from haystack.components.embedders import OpenAITextEmbedder
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack.utils import Secret
from dotenv import load_dotenv
import os
import time
import json

# Initialize Weights and Biases
wandb.init(project="haystack-indexing", config={"task": "Indexing Pipeline"})

load_dotenv(".env")
open_ai_key = os.environ.get("OPENAI_API_KEY")

# Initialize ElasticsearchDocumentStore and embedder
document_store = ElasticsearchDocumentStore(hosts="http://localhost:9200")
text_embedder = OpenAITextEmbedder(api_key=Secret.from_token(open_ai_key))

# Load dataset and log dataset metadata
with open("news_out.jsonl", 'r') as file:
    data = [json.loads(line) for line in file]
wandb.config.update({"dataset_size": len(data)})

# Indexing pipeline
def indexing_pipeline(data):
    documents = []
    for entry in data:
        start_time = time.time()
        
        # Embed text and log embedding time
        embedding = text_embedder.embed({"text": entry["content"]})
        end_time = time.time()
        
        # Log individual document metrics
        wandb.log({
            "embedding_time": end_time - start_time,
            "document_length": len(entry["content"]),
            "embedding_status": "success" if embedding else "failure"
        })
        
        # Create document and store in Elasticsearch
        document = {
            "content": entry["content"],
            "meta": entry
        }
        document_store.write_documents([document])

        # Add to document list for summary logging
        documents.append(document)
    
    wandb.log({"total_documents_indexed": len(documents)})

# Run the indexing pipeline
indexing_pipeline(data)

wandb.finish()
