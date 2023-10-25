import pytest
import os
from haystack.preview import Pipeline
from haystack.preview.components.builders.prompt_builder import PromptBuilder
from haystack.preview.components.generators.openai.gpt import GPTGenerator
from dotenv import load_dotenv
from ..scripts.pipelines import initialize_simple_pipeline

load_dotenv()
load_dotenv("./../../.env")

def test_env_variable():
    """Test if OPENAI_API_KEY environment variable is set."""
    openai_key = os.getenv("OPENAI_API_KEY")
    assert openai_key is not None, "Please set OPENAI_API_KEY as an environment variable."

def test_pipeline_initialization():
    """Test the initialization of the pipeline."""
    prompt_template = "Test template"
    gpt = GPTGenerator(api_key=os.getenv("OPENAI_API_KEY"), model_name='gpt-4', api_base_url='https://api.openai.com/v1')
    
    # Try initializing the pipeline
    try:
        pipeline = initialize_simple_pipeline(llm_generator=gpt, llm_generator_name="gpt_generator", prompt_template=prompt_template)
    except Exception as e:
        pytest.fail(f"Pipeline initialization failed: {e}")
    
    assert pipeline is not None, "Pipeline should be initialized."

def test_pipeline_execution():
    """Test the execution of a question through the pipeline."""
    prompt_template = """
        Given a question, you provide with an accurate answer using Shakespeare's style. Begin with the word 'Answer:' in your answer.
        \nQuestion: {{question}}
        \nAnswer:
        """
    gpt = GPTGenerator(api_key=os.getenv("OPENAI_API_KEY"), model_name='gpt-4', api_base_url='https://api.openai.com/v1')
    pipeline = initialize_simple_pipeline(llm_generator=gpt, llm_generator_name="gpt_generator", prompt_template=prompt_template)
    
    question = "What is the capital of France?"
    result = pipeline.run(
        {
            "prompt_builder": {"question": question},
        }
    )
    
    assert result is not None, "Result should not be None."
    assert 'replies' in result['gpt_generator'].keys(), "Result should contain an 'answer'."
    assert len(result['gpt_generator']['replies']) > 0, "Result should contain at least one 'answer'."



