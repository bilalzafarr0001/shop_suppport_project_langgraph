"""
graph.py — connect all the steps into one graph.
"""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore
from langgraph.types import RetryPolicy

from nodes import (State, check_mood, faq_specialist, find_issues, load_history, manager_approval,
                   order_specialist, plan_work, product_specialist, quality_check, refund_specialist,
                   rewrite_reply, save_history, send_to_specialists, write_reply)

builder = StateGraph(State)

# ---------- add every node ----------
builder.add_node("load_history", load_history)
builder.add_node("find_issues", find_issues, retry_policy=RetryPolicy(max_attempts=3))  # try again if it fails
builder.add_node("check_mood", check_mood)
builder.add_node("plan_work", plan_work)
builder.add_node("order_specialist", order_specialist)
builder.add_node("refund_specialist", refund_specialist)
builder.add_node("faq_specialist", faq_specialist)
builder.add_node("product_specialist", product_specialist)
builder.add_node("manager_approval", manager_approval)
builder.add_node("write_reply", write_reply)
builder.add_node("quality_check", quality_check)
builder.add_node("rewrite_reply", rewrite_reply)
builder.add_node("save_history", save_history)

# ---------- STEP 1: three nodes start at the same time ----------
builder.add_edge(START, "load_history")
builder.add_edge(START, "find_issues")
builder.add_edge(START, "check_mood")
builder.add_edge(["load_history", "find_issues", "check_mood"], "plan_work")   # waits for all 3

# ---------- STEP 2: one specialist per problem (conditional edge + Send) ----------
builder.add_conditional_edges("plan_work", send_to_specialists,
                              ["order_specialist", "refund_specialist", "faq_specialist",
                               "product_specialist", "write_reply"])

# ---------- STEP 3: all specialists finish -> manager approval ----------
builder.add_edge("order_specialist", "manager_approval")
builder.add_edge("refund_specialist", "manager_approval")
builder.add_edge("faq_specialist", "manager_approval")
builder.add_edge("product_specialist", "manager_approval")

# ---------- STEP 4: write the email and check it ----------
builder.add_edge("manager_approval", "write_reply")
builder.add_edge("write_reply", "quality_check")
builder.add_edge("rewrite_reply", "quality_check")   # loop back for another check
# quality_check chooses its next node itself (Command), so it has no edges here

# ---------- STEP 5: remember the customer, then finish ----------
builder.add_edge("save_history", END)

# checkpointer = saves every step (needed to pause for the manager)
# store        = long-term memory about each customer
graph = builder.compile(checkpointer=InMemorySaver(), store=InMemoryStore())
