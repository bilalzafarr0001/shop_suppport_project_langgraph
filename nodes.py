"""
nodes.py — the STATE and every STEP of the main graph, in order.

A node is a normal function:
  - it gets the state (the shared notebook)
  - it returns only the parts it changed
"""

import operator
from typing import Annotated, Literal, TypedDict

from langchain.agents import create_agent
from langgraph.config import get_store
from langgraph.types import Command, Send, interrupt

from llm import IssueList, Review, llm, mood_chain, reply_chain, rewrite_chain
from product_team import product_team
from rag import answer_from_policies
from refund_team import refund_team
from tools import CUSTOMERS, MCP_TOOLS, ORDERS


# ======================= THE STATE (shared notebook) =======================
class State(TypedDict):
    customer_id: str
    ticket: str          # the customer's message
    history: str         # what we remember about this customer
    mood: str            # calm, upset or angry
    issues: list         # the problems found in the message
    answers: Annotated[list, operator.add]       # many specialists ADD answers at the same time
    big_refunds: Annotated[list, operator.add]   # refunds that need a manager's OK
    reply: str           # the email we send back
    feedback: str        # what to fix in the email
    tries: int           # how many times we fixed the email


# ======================= STEP 1: three jobs at the same time =======================

def load_history(state):
    store = get_store()   # long-term memory
    saved = store.get(("customers", state["customer_id"]), "history")
    if saved is None:
        return {"history": "first time contacting us"}
    return {"history": saved.value["text"]}


def find_issues(state):
    result = llm.with_structured_output(IssueList).invoke(
        "Find every separate problem in this customer message:\n" + state["ticket"])
    issues = []
    for issue in result.issues:
        issues.append(issue.model_dump())   # turn each form into a normal dict
    return {"issues": issues}


def check_mood(state):
    mood = mood_chain.invoke({"ticket": state["ticket"]})
    return {"mood": mood.strip().lower()}


# ======================= STEP 2: give each problem to a specialist =======================

def plan_work(state):
    print(f"   -> found {len(state['issues'])} problem(s), customer is {state['mood']}")
    return {}


SPECIALIST_FOR = {
    "order_status": "order_specialist",
    "refund": "refund_specialist",
    "policy_question": "faq_specialist",
    "product_question": "product_specialist",
}


# A conditional edge. Send = start one specialist for EACH problem, all at the same time.
def send_to_specialists(state):
    if len(state["issues"]) == 0:
        return "write_reply"   # nothing to solve, just reply
    jobs = []
    for issue in state["issues"]:
        specialist = SPECIALIST_FOR[issue["kind"]]
        jobs.append(Send(specialist, {"issue": issue, "customer_id": state["customer_id"]}))
    return jobs


# --- Specialist 1: a ready-made agent that uses the MCP order tools ---
# MCP tools only work with "async", so this function is "async def" and uses "await".
async def order_specialist(job):
    order_id = job["issue"]["order_id"]
    order = ORDERS.get(order_id)
    if order is None or order["customer_id"] != job["customer_id"]:
        return {"answers": [f"Order {order_id}: not found on this customer's account."]}

    agent = create_agent(llm, tools=MCP_TOOLS, system_prompt="Check orders with your tools. Answer in 2 short lines.")
    result = await agent.ainvoke({"messages": [("user", f"What is the status of order {order_id}?")]})
    return {"answers": [f"Order {order_id}: " + result["messages"][-1].content]}


# --- Specialist 2: the refund team (a subgraph) ---
def refund_specialist(job):
    result = refund_team.invoke({"order_id": job["issue"]["order_id"], "customer_id": job["customer_id"]})
    if result["approved"] and result["amount"] > 100:
        return {"big_refunds": [result["message"]]}   # too big: a manager must say yes
    if result["approved"]:
        return {"answers": ["Refund approved: " + result["message"] + ". Money arrives in 5-7 days."]}
    return {"answers": ["Refund not possible: " + result["message"]]}


# --- Specialist 3: RAG on the policy documents ---
def faq_specialist(job):
    answer = answer_from_policies(job["issue"]["detail"])
    return {"answers": ["Policy: " + answer]}


# --- Specialist 4: the agent we built by hand ---
def product_specialist(job):
    result = product_team.invoke({"messages": [("user", job["issue"]["detail"])]})
    return {"answers": ["Product: " + result["messages"][-1].content]}


# ======================= STEP 3: manager approval (human in the loop) =======================

def manager_approval(state):
    if len(state["big_refunds"]) == 0:
        return {}   # nothing to approve

    question = "Approve: " + ", ".join(state["big_refunds"]) + "? (yes/no)"
    answer = interrupt(question)   # the graph PAUSES here until the manager answers

    if answer == "yes":
        approved = []
        for refund in state["big_refunds"]:
            approved.append("Refund approved: " + refund + ". Money arrives in 5-7 days.")
        return {"answers": approved}
    return {"answers": ["Refund: a manager will review it and email you within 24 hours."]}


# ======================= STEP 4: write the email and check it =======================

def write_reply(state):
    answers = "\n".join(state["answers"])
    if answers == "":
        answers = "No problem found. Thank the customer and offer help."
    reply = reply_chain.invoke({
        "name": CUSTOMERS[state["customer_id"]],
        "history": state["history"],
        "mood": state["mood"],
        "ticket": state["ticket"],
        "answers": answers,
    })
    return {"reply": reply}


# Command = the node itself chooses the next node.
# The line "-> Command[...]" just tells LangGraph which nodes it can go to.
def quality_check(state) -> Command[Literal["rewrite_reply", "save_history"]]:
    review = llm.with_structured_output(Review).invoke(
        f"Customer message: {state['ticket']}\n\nOur email:\n{state['reply']}\n\n"
        "Is the email polite, and does it answer every point?")
    print(f"   -> quality check: good = {review.is_good}")

    if review.is_good or state["tries"] >= 2:
        return Command(goto="save_history")
    return Command(goto="rewrite_reply", update={"feedback": review.feedback})


def rewrite_reply(state):
    better = rewrite_chain.invoke({"reply": state["reply"], "feedback": state["feedback"]})
    return {"reply": better, "tries": state["tries"] + 1}


# ======================= STEP 5: remember this customer =======================

def save_history(state):
    store = get_store()
    topics = []
    for issue in state["issues"]:
        topics.append(issue["kind"])
    if len(topics) == 0:
        topics.append("a general question")
    note = "Last time asked about: " + ", ".join(topics) + ". Mood was " + state["mood"] + "."
    store.put(("customers", state["customer_id"]), "history", {"text": note})
    return {}
