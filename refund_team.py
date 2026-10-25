"""
refund_team.py — a SUBGRAPH (a small graph used inside the big graph).

It checks the refund rules with plain Python. No AI here, because money must be exact.

    START -> find_order -> (follows the rules?) -> approve -> END
                                                -> reject  -> END
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from tools import ORDERS


class RefundState(TypedDict):
    order_id: str
    customer_id: str
    order: dict
    approved: bool
    amount: int
    message: str


def find_order(state):
    order = ORDERS.get(state["order_id"])
    # Safety: a customer can only get a refund for their OWN order
    if order is None or order["customer_id"] != state["customer_id"]:
        return {"order": {}}
    return {"order": order}


# A conditional edge: returns the NAME of the next node
def follows_rules(state):
    order = state["order"]
    if order and order["status"] == "delivered" and order["days_since_delivery"] <= 30:
        return "approve"
    return "reject"


def approve(state):
    order = state["order"]
    return {"approved": True, "amount": order["price"],
            "message": f"${order['price']} refund for the {order['item']}"}


def reject(state):
    order = state["order"]
    if state["order_id"] == "":
        reason = "Please send us your order number."
    elif not order:
        reason = f"Order {state['order_id']} is not on your account."
    elif order["status"] != "delivered":
        reason = f"Order {state['order_id']} is not delivered yet, so it can't be refunded."
    else:
        reason = f"Order {state['order_id']} was delivered more than 30 days ago."
    return {"approved": False, "amount": 0, "message": reason}


builder = StateGraph(RefundState)
builder.add_node("find_order", find_order)
builder.add_node("approve", approve)
builder.add_node("reject", reject)

builder.add_edge(START, "find_order")
builder.add_conditional_edges("find_order", follows_rules, ["approve", "reject"])
builder.add_edge("approve", END)
builder.add_edge("reject", END)

refund_team = builder.compile()
