"""
main.py — START HERE:   python main.py

You type messages as a customer.
If a big refund needs approval, you answer as the manager.
"""

import asyncio
import sys
import uuid

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.types import Command

from graph import graph
from tools import MCP_TOOLS


# ---------- 1. Start the MCP server and get its tools ----------
def load_mcp_tools():
    client = MultiServerMCPClient({
        "shop": {"command": sys.executable, "args": ["mcp_server.py"], "transport": "stdio"},
    })
    tools = asyncio.run(client.get_tools())
    MCP_TOOLS.extend(tools)
    print("MCP tools:", [tool.name for tool in tools])

    # MCP can also share text (a resource) and ready-made prompts
    info = asyncio.run(client.get_resources("shop", uris=["shop://store-info"]))
    print("MCP resource:", info[0].as_string())
    prompt = asyncio.run(client.get_prompt("shop", "apology_prompt", arguments={"customer_name": "Alex"}))
    print("MCP prompt:", prompt[0].content)


# ---------- 2. Run the graph and print each step when it finishes (streaming) ----------
async def run_graph(data, config):
    async for step in graph.astream(data, config, stream_mode="updates"):
        for node_name in step:
            if node_name != "__interrupt__":
                print("[done]", node_name)


# ---------- 3. Handle one customer message ----------
def handle_message(customer_id, message):
    # thread_id = the id of this conversation (the checkpointer saves it)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # The notebook (state) at the start
    start = {"customer_id": customer_id, "ticket": message, "answers": [], "big_refunds": [], "tries": 0}
    asyncio.run(run_graph(start, config))

    # Did the graph pause for the manager?
    state = graph.get_state(config)
    if state.interrupts:
        question = state.interrupts[0].value
        answer = input(f"\nMANAGERRRR, {question} ")
        asyncio.run(run_graph(Command(resume=answer.strip().lower()), config))   # continue
        state = graph.get_state(config)

    print("\n----------- EMAIL TO CUSTOMER -----------")
    print(state.values["reply"])
    print("-----------------------------------------")


# ---------- 4. The chat ----------
load_mcp_tools()
customer_id = "C-100"

print("""
You are customer Alex (C-100). Try:
  Where is my order 1002?
  I want a refund for order 1001. Do you accept cash on delivery?
  This is the worst! Order 1002 is late and I want my money back for order 1003!
  Is the smart watch in stock?
Type 'sara' or 'alex' to change customer. Type 'quit' to stop.
""")

while True:
    message = input("\nCustomer: ").strip()
    if message == "quit":
        break
    elif message == "alex":
        customer_id = "C-100"
        print("You are now Alex.")
    elif message == "sara":
        customer_id = "C-200"
        print("You are now Sara.")
    elif message != "":
        handle_message(customer_id, message)
