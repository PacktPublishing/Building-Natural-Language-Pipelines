import threading
from bytewax.run import cli_main
from chatbot import graph
from dataflow import create_dataflow

def run_dataflow():
    flow = create_dataflow()
    cli_main(flow)

def run_chatbot():
    print("Chatbot with real-time data. Type 'quit' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break
        state = {"messages": [("user", user_input)]}
        events = graph.stream(state)
        for event in events:
            for key, value in event.items():
                print(f"Assistant: {value['messages'][-1][1]}")

if __name__ == "__main__":
    # Run dataflow in a separate thread
    dataflow_thread = threading.Thread(target=run_dataflow)
    dataflow_thread.daemon = True
    dataflow_thread.start()

    # Run chatbot
    run_chatbot()
