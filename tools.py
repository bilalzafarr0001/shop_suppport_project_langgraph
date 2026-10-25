"""
tools.py — the store's data, and the tools the AI can use.
A tool is a normal function. Its docstring tells the AI when to use it.
"""

import json

from langchain_core.tools import tool

# The orders "database"
with open("data/orders.json") as file:
    ORDERS = json.load(file)

CUSTOMERS = {"C-100": "Alex", "C-200": "Sara"}

PRODUCTS = {
    "running shoes": {"price": 85, "stock": 12},
    "wireless headphones": {"price": 150, "stock": 0},
    "smart watch": {"price": 220, "stock": 4},
    "phone case": {"price": 15, "stock": 50},
    "laptop bag": {"price": 60, "stock": 7},
}


@tool
def check_product(name: str) -> str:
    """Get the price and stock of one product."""
    for product_name in PRODUCTS:
        if name.lower() in product_name:
            info = PRODUCTS[product_name]
            return f"{product_name}: ${info['price']}, {info['stock']} in stock"
    return "Product not found."


@tool
def list_products() -> str:
    """List all the products in the store."""
    return ", ".join(PRODUCTS)


# Tools that come from the MCP server. main.py fills this list when the app starts.
MCP_TOOLS = []
