from langchain.tools import Tool
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from bytewax.run import cli_main
from dataflow import create_dataflow
from dotenv import load_dotenv
load_dotenv(".env")
import os 

openaiapi_key = os.getenv("OPENAI_API_KEY")

def run_dataflow(percentage):
    print(percentage)
    flow = create_dataflow( percentage)
    cli_main(flow)
    
# Define the LangChain tool
dataflow_tool = Tool(
    name="Coinbase Dataflow",
    description="Executes the Coinbase dataflow to analyze order book states. Input is percentage for filtering large spreads.",
    func=lambda input_text: run_dataflow(*input_text.split(","))
)

# Initialize a language model for the agent
llm = ChatOpenAI(model="gpt-4o-mini", api_key=openaiapi_key)


# Initialize the agent with the tool
agent = initialize_agent(
    tools=[dataflow_tool],
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

# Ask a question or give a command
user_query = "Run the Coinbase dataflow with a spread filter of 0.0001"
response = agent.run(user_query)

print(response)