"""
mcp_server.py — the store's ORDER SYSTEM, shared through MCP.

MCP = a standard way to give tools to any AI app.
This file is a separate program. main.py starts it in the background.
"""

import json

from mcp.server.fastmcp import FastMCP

with open("data/orders.json") as file:
    ORDERS = json.load(file)

mcp = FastMCP("ShopSystem")


# A TOOL: the AI can call it
@mcp.tool()
def get_order_status(order_id: str) -> str:
    """Get the status of an order. order_id is a number like 1002."""
    order = ORDERS.get(order_id)
    if order is None:
        return "Order not found."
    return f"{order['item']} is {order['status']}. Tracking: {order['tracking']}. Arrives: {order['arrives']}."


# A RESOURCE: read-only text
@mcp.resource("shop://store-info")
def store_info() -> str:
    """Store opening hours and contact."""
    return "ShopEasy support is open 9 AM to 9 PM. Email: support@shopeasy.example"


# A PROMPT: a ready-made prompt
@mcp.prompt()
def apology_prompt(customer_name: str) -> str:
    """A ready-made apology prompt."""
    return f"Write a short, kind apology to {customer_name}."


if __name__ == "__main__":
    mcp.run(transport="stdio")
