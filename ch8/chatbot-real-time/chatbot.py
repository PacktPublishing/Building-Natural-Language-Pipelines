from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_anthropic import ChatAnthropic

# Chatbot state
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]

# LangGraph chatbot
graph_builder = StateGraph(ChatState)

llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")


def chatbot(state: ChatState):
    user_message = state["messages"][-1][1]
    if "BTC-USD" in user_message:
        # Fetch real-time data (mocked for this example)
        best_bid = 30000
        best_ask = 30010
        response = f"The best bid is ${best_bid} and the best ask is ${best_ask}."
    else:
        response = llm.invoke(state["messages"])
    return {"messages": [("assistant", response)]}


graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()
