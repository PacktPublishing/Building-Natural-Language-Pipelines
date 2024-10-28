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
wandb.init(project="haystack-querying-feedback-loop", config={"task": "Query Pipeline with RAGAS Evaluation and Feedback Loop"})

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

# Define RAGAS evaluation component
evaluator_context = RagasEvaluator(metric=RagasMetric.CONTEXT_PRECISION)

# Custom feedback loop component
@component
class FeedbackLoopValidator:
    def __init__(self, score_threshold: float = 0.9):
        self.score_threshold = score_threshold
        self.iteration_counter = 0

    @component.output_types(valid_replies=str, regenerate_flag=bool)
    def run(self, replies: str, context_precision_score: float):
        self.iteration_counter += 1
        # Check if score meets the threshold
        if context_precision_score >= self.score_threshold:
            print(f"Iteration {self.iteration_counter}: Score {context_precision_score} is sufficient.")
            return {"valid_replies": replies, "regenerate_flag": False}
        else:
            print(f"Iteration {self.iteration_counter}: Score {context_precision_score} is below threshold; regenerating.")
            return {"valid_replies": None, "regenerate_flag": True}

feedback_validator = FeedbackLoopValidator(score_threshold=0.9)

# Build the Pipeline with feedback loop
query_pipeline = Pipeline(max_runs_per_component=5)
query_pipeline.add_component("text_embedder", text_embedder)
query_pipeline.add_component("retriever", retriever)
query_pipeline.add_component("prompt_builder", prompt_builder)
query_pipeline.add_component("llm", generator)
query_pipeline.add_component("evaluator_context", evaluator_context)
query_pipeline.add_component("feedback_validator", feedback_validator)

# Connect components
query_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
query_pipeline.connect("retriever", "prompt_builder.documents")
query_pipeline.connect("prompt_builder", "llm")
query_pipeline.connect("llm.replies", "evaluator_context.responses")
query_pipeline.connect("retriever", "evaluator_context.contexts")
query_pipeline.connect("evaluator_context.results", "feedback_validator.context_precision_score")
query_pipeline.connect("llm.replies", "feedback_validator.replies")

# Connect feedback loop to retry prompt if the score is low
query_pipeline.connect("feedback_validator.regenerate_flag", "prompt_builder.regenerate_flag")

# Example evaluation data
EVALUATION_DATA = [
    {
        "question": "What was the new price target set by Piper Sandler for Virtus Inv?",
        "context": ["Piper Sandler analyst Crispin Love maintains Virtus Inv (NYSE:VRTS) with an Overweight rating and raises the price target from $265 to $267."],
        "ground_truth": "Virtus Inv's price target was raised to $267 by Piper Sandler."
    },
    {
        "question": "What details did Faraday Future plan to reveal about its US-China automotive strategy?",
        "context": ["Faraday Future is set to share details of its 'US-China Automotive Industry Bridge Strategy,' including Phase 1, in the coming months."],
        "ground_truth": "Faraday Future will share details about its US-China bridge strategy and Phase 1 soon."
    },
]

# Run evaluations
for example in EVALUATION_DATA:
    question = example["question"]
    context = example["context"]
    ground_truth = example["ground_truth"]
    
    start_time = time.time()
    results = query_pipeline.run({
        "text_embedder": {"text": question},
        "prompt_builder": {"question": question},
        "evaluator_context": {
            "questions": [question],
            "contexts": [context],
            "ground_truths": [ground_truth]
        }
    })
    end_time = time.time()

    # Log results and metrics
    context_precision_score = results["evaluator_context"]["results"][0]["score"]
    wandb.log({
        "query_time": end_time - start_time,
        "context_precision_score": context_precision_score,
        "embedding_token_usage": results['text_embedder']['meta']['usage']['total_tokens'],
        "llm_prompt_token_usage": results['llm']['meta'][0]['usage']['prompt_tokens'],
        "llm_completion_token_usage": results['llm']['meta'][0]['usage']['completion_tokens'],
        "llm_total_token_usage": results['llm']['meta'][0]['usage']['total_tokens']
    })

    # Print evaluation results
    print(f"Context Precision Score: {context_precision_score}")
    print(f"Response: {results['llm']['replies'][0]}")

wandb.finish()
