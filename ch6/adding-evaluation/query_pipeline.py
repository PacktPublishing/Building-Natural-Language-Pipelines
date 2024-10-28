from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack import Pipeline
from haystack.components.embedders import OpenAITextEmbedder
from haystack.utils import Secret
from haystack_integrations.components.retrievers.elasticsearch import ElasticsearchEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack_integrations.components.evaluators.ragas import RagasEvaluator, RagasMetric

from dotenv import load_dotenv
import os
import wandb
import time

# Load environment variables
load_dotenv(".env")
open_ai_key = os.environ.get("OPENAI_API_KEY")
os.environ["WANDB_API_KEY"] = os.getenv("WANDB_API_KEY")
wandb.init(project="haystack-querying-evaluation", config={"task": "Query Pipeline with RAGAS Evaluation"})

# Initialize ElasticsearchDocumentStore
document_store = ElasticsearchDocumentStore(hosts="http://localhost:9200")

# Initialize components
text_embedder = OpenAITextEmbedder(api_key=Secret.from_token(open_ai_key))
retriever = ElasticsearchEmbeddingRetriever(document_store=document_store)

# Define prompt template
template = """
Given the following information, answer the question.
Context:
{% for document in documents %}
{{ document.content }}
{% endfor %}
Question: {{question}}
Answer:
"""
prompt_builder = PromptBuilder(template=template)
generator = OpenAIGenerator(model="gpt-4o-mini", api_key=Secret.from_token(open_ai_key))

# Define RAGAS evaluation components
evaluator_context = RagasEvaluator(metric=RagasMetric.CONTEXT_PRECISION)
evaluator_aspect = RagasEvaluator(
    metric=RagasMetric.ASPECT_CRITIQUE,
    metric_params={"name": "child_friendly", "definition": "Is this answer understandable for a general audience?", "strictness": 2},
)

# Build the Pipeline
query_pipeline = Pipeline()
query_pipeline.add_component("text_embedder", text_embedder)
query_pipeline.add_component("retriever", retriever)
query_pipeline.add_component("prompt_builder", prompt_builder)
query_pipeline.add_component("llm", generator)
query_pipeline.add_component("evaluator_context", evaluator_context)
query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
query_pipeline.connect("retriever", "prompt_builder.documents")
query_pipeline.connect("prompt_builder", "llm")
# To use aspect critique evaluation, uncomment the following lines
# query_pipeline.add_component("evaluator_aspect", evaluator_aspect)
# remove or comment out the following line
query_pipeline.connect("llm.replies", "evaluator_context.ground_truths")

query_pipeline.draw(path="query_pipeline_ragas.png")

# Example evaluation data
EVALUATION_DATA = [
    {
        "question": "What was the new price target set by Piper Sandler for Virtus Inv?",
        "context": ["Piper Sandler analyst Crispin Love maintains Virtus Inv (NYSE:VRTS) with an Overweight rating and raises the price target from $265 to $267."],
        "response": "Piper Sandler raised the price target for Virtus Inv to $267.",
        "ground_truth": "Virtus Inv's price target was raised to $267 by Piper Sandler."
    },
    {
        "question": "What details did Faraday Future plan to reveal about its US-China automotive strategy?",
        "context": ["Faraday Future is set to share details of its 'US-China Automotive Industry Bridge Strategy,' including Phase 1, in the coming months."],
        "response": "Faraday Future plans to reveal Phase 1 of its US-China strategy soon.",
        "ground_truth": "Faraday Future will share details about its US-China bridge strategy and Phase 1 soon."
    },
    # Add more examples as needed
]

# Run evaluations
for example in EVALUATION_DATA:
    start_time = time.time()
    results = query_pipeline.run({
        "text_embedder": {"text": example["question"]},
        "prompt_builder": {"question": example["question"]},
        "evaluator_context": {
            "questions": [example["question"]],
            "contexts": [example["context"]],  # Provide 'contexts' input here
        }
    })

    end_time = time.time()

    # Log results and metrics
    wandb.log({
        "query_time": end_time - start_time,
        "context_precision_score": results["evaluator_context"]["results"][0][0]["score"],
        # "aspect_critique_score": results["evaluator_aspect"]["results"][0][0]["score"],
        "embedding_token_usage": results['text_embedder']['meta']['usage']['total_tokens'],
        "llm_prompt_token_usage": results['llm']['meta'][0]['usage']['prompt_tokens'],
        "llm_completion_token_usage": results['llm']['meta'][0]['usage']['completion_tokens'],
        "llm_total_token_usage": results['llm']['meta'][0]['usage']['total_tokens']
    })

    # Print evaluation results
    print(f"Context Precision Score: {results['evaluator_context']['results'][0][0]['score']}")
    # print(f"Aspect Critique Score: {results['evaluator_aspect']['results'][0][0]['score']}")

wandb.finish()
