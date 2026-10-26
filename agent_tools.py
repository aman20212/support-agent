from datetime import date


# Fake order data, standing in for a database for now
ORDERS = {
    "1001": {"item": "Wireless mouse", "amount": 1499, "status": "delivered", "delivered_on": "2026-10-05"},
    "1002": {"item": "Laptop stand",   "amount": 2499, "status": "delivered", "delivered_on": "2026-10-03"},
    "1003": {"item": "USB-C cable",    "amount": 599,  "status": "shipped",   "delivered_on": None},
    "1004": {"item": "Desk lamp", "amount": 1899, "status": "delivered", "delivered_on": "2026-09-20"}
}

TODAY = date(2026, 10, 9)        # fixed on purpose, so tests give the same result every day
REFUND_WINDOW_DAYS = 7           # refunds allowed within 7 days of delivery

TICKETS = []                     # support tickets, kept in memory only
REFUNDS = {}                     # order_id -> amount already refunded

def look_up_order(order_id):             # a normal Python function, no AI in it
    order = ORDERS.get(order_id)         # returns None if the id is not there
    if order is None:
        return {"error": f"No order found with id {order_id}"}
    return order

def check_refund_rules(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return {"eligible": False, "reason": f"No order found with id {order_id}"}
    if order["status"] != "delivered":
        return {"eligible": False, "reason": "Order has not been delivered yet"}
    days = (TODAY - date.fromisoformat(order["delivered_on"])).days
    if days > REFUND_WINDOW_DAYS:
        return {"eligible": False,
                "reason": f"Delivered {days} days ago; window is {REFUND_WINDOW_DAYS} days"}
    return {"eligible": True, "reason": f"Delivered {days} days ago, within the window"}


def create_ticket(order_id, issue):
    if order_id not in ORDERS:
        return {"error": f"No order found with id {order_id}"}
    ticket_id = f"T-{len(TICKETS) + 1}"
    TICKETS.append({"ticket_id": ticket_id, "order_id": order_id, "issue": issue})
    return {"ticket_id": ticket_id, "status": "open"}

def refund_precheck(order_id, amount):
    """Hard rules, enforced by CODE. Returns a problem string, or None if all is fine."""
    rules = check_refund_rules(order_id)
    if not rules["eligible"]:                       # rule 1: order must be eligible
        return rules["reason"]
    try:
        amount = float(amount)                      # rule 2: amount must be a number
    except (TypeError, ValueError):
        return "Amount must be a number"
    if amount <= 0 or amount > ORDERS[order_id]["amount"]:
        return f"Amount must be more than 0 and at most {ORDERS[order_id]['amount']}"
    if order_id in REFUNDS:                         # rule 3: no second refund
        return "This order has already been refunded"
    return None                                     # None means: no problem found


def issue_refund(order_id, amount):
    problem = refund_precheck(order_id, amount)     # check again, never trust the caller
    if problem:
        return {"error": problem}
    REFUNDS[order_id] = float(amount)               # "move the money"
    return {"refund_id": f"R-{len(REFUNDS)}", "order_id": order_id, "refunded": float(amount)}



# The menu the model sees (same as Step 2)
TOOLS = [
        {
        "type": "function",
        "function": {
            "name": "look_up_order",
            "description": "Get the details of one customer order (item, amount, "
                           "status, delivery date) using its order id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order id, for example 1002"}
                },
                "required": ["order_id"],
            },
        },
    },
      {
        "type": "function",
        "function": {
            "name": "check_refund_rules",
            "description": "Check whether an order is eligible for a refund under store policy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order id"}
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Open a support ticket for a problem with an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order id"},
                    "issue": {"type": "string", "description": "Short description of the problem"},
                },
                "required": ["order_id", "issue"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "issue_refund",
            "description": "Refund money for an order. Only call this after check_refund_rules says the order is eligible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order id"},
                    "amount": {"type": "number", "description": "Amount in rupees to refund"},
                },
                "required": ["order_id", "amount"],
            },
        },
    },
]

# Name on the menu -> the real function. Your code uses this to find what to run.
TOOL_FUNCTIONS = {
    "look_up_order": look_up_order,
    "check_refund_rules": check_refund_rules,
    "create_ticket": create_ticket,
    "issue_refund": issue_refund,
}

NEEDS_APPROVAL = {"issue_refund"}                 # tools that must wait for a human
PRECHECKS = {"issue_refund": refund_precheck}     # hard rules, run BEFORE asking the human


print("Agent tools loaded:", ", ".join(f"{name}()" for name in TOOL_FUNCTIONS))