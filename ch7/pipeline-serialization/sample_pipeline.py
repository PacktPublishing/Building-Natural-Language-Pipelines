from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import HuggingFaceLocalChatGenerator
from haystack import Pipeline 
from dotenv import load_dotenv
import os

template = [ChatMessage.from_system("""
                            Please create a summary about the following topic:
                            {{ topic }}
                """)]
prompt_builder = ChatPromptBuilder(template=template)
llm = HuggingFaceLocalChatGenerator(model="Qwen/Qwen2.5-1.5B-Instruct", generation_kwargs={"max_new_tokens": 150})


# Inititalize pipeline
pipe = Pipeline()
# Add components
pipe.add_component(instance=prompt_builder, name="prompt_builder")
pipe.add_component(instance=llm, name="llm" )
pipe.connect("prompt_builder.prompt", "llm.messages")

response = pipe.run({"prompt_builder": {"topic": "The history of the internet"}})
print(response)

# Serialize the pipeline
yaml_pipeline = pipe.dumps()

# Save the pipeline to a file
with open("chat_pipeline.yaml", "w") as f:
    f.write(yaml_pipeline)