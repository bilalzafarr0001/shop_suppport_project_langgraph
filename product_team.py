"""
product_team.py — an AI AGENT built by hand (a small graph).

This is what every AI agent does inside:
  agent: the AI thinks. If it needs data, it asks for a tool.
  tools: runs that tool, then goes back to the agent.
  When the AI doesn't ask for a tool anymore, it is finished.

    START -> agent -> (asked for a tool?) -> yes -> tools -> back to agent
                                          -> no  -> END
"""

from typing import Annotated, TypedDict

from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from llm import llm
from tools import check_product, list_products


class ProductState(TypedDict):
    messages: Annotated[list, add_messages]   # add_messages = keep adding to the chat


product_tools = [check_product, list_products]
llm_with_tools = llm.bind_tools(product_tools)   # tell the AI which tools it can ask for


def agent(state):
    answer = llm_with_tools.invoke(state["messages"])
    return {"messages": [answer]}


builder = StateGraph(ProductState)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(product_tools))   # ToolNode runs the tool the AI asked for

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)   # tool asked? go to "tools". If not: END
builder.add_edge("tools", "agent")

product_team = builder.compile()
