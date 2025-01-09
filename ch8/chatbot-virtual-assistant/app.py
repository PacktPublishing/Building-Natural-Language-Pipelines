import chainlit as cl
from dotenv import load_dotenv
import os 
from rag_pipeline import tools, rag_pipeline_func
import json
from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.generators.utils import print_streaming_chunk

# Load environment variables (if any)
load_dotenv(".env")
open_ai_key = os.getenv("OPENAI_API_KEY")



@cl.on_message
async def main(message: str):

    messages = [
    ChatMessage.from_system(
        "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."
    ),
    ChatMessage.from_user(message.content),
]

    chat_generator = OpenAIChatGenerator(model="gpt-4o-mini", streaming_callback=print_streaming_chunk)
    response = chat_generator.run(messages=messages, generation_kwargs={"tools": tools})
    function_call = json.loads(response["replies"][0].text)[0]
    function_name = function_call["function"]["name"]
    function_args = json.loads(function_call["function"]["arguments"])

    ## Find the correspoding function and call it with the given arguments
    available_functions = {"rag_pipeline_func": rag_pipeline_func}
    function_to_call = available_functions[function_name]
    function_response = function_to_call(**function_args)
    print(function_response)
    answer = function_response['reply']

    msg_content = str(answer) if isinstance(answer, str) else getattr(answer, "text", None) or json.dumps(answer)
    msg = cl.Message(content=msg_content)

    # Send the message to the user
    await msg.send()