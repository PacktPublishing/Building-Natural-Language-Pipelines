from haystack.preview import Pipeline
from haystack.preview.components.builders.prompt_builder import PromptBuilder

def initialize_simple_pipeline(llm_generator, llm_generator_name, prompt_template):
    # Creating a pipeline
    pipeline = Pipeline()

    # Adding a PromptBuilder
    prompt_builder = PromptBuilder(template=prompt_template)
    pipeline.add_component(instance=prompt_builder, name="prompt_builder")

    # Adding a GPT-based Generator
    # Ensure that you have the OPENAI_API_KEY environment variable set
    gpt_generator = llm_generator # GPTGenerator(api_key=os.environ.get("OPENAI_API_KEY"))
    pipeline.add_component(instance=gpt_generator, name=llm_generator_name) #"gpt_generator")

    # Connecting the components
    pipeline.connect("prompt_builder",llm_generator_name)

    return pipeline