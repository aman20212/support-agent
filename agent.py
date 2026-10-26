import os
import json
import httpx
from dotenv import load_dotenv
from agent_tools import TOOLS, TOOL_FUNCTIONS, NEEDS_APPROVAL, PRECHECKS
from datetime import datetime

load_dotenv()
URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
    "Content-Type": "application/json",
}
MODEL = "openai/gpt-oss-20b"
WRITE_TOOLS = {"create_ticket", "issue_refund"}    # tools that change something

MAX_STEPS = 4                               # safety cap, set by YOU

SYSTEM_PROMPT = (
    "You are a support agent for an online store. Use the tools to get facts. "
    "Never guess order details. For a refund request: look up the order, check the "
    "refund rules, open a ticket, and if the order is eligible, call the issue_refund "
    "tool yourself. The system itself will ask a human to approve it, so do not say "
    "it will be reviewed by another team. Only say a refund was issued if issue_refund "
    "returned a refund_id. If a tool returns an error or a human declines, tell the "
    "user plainly and do not retry. Do not promise anything you cannot do, such as "
    "follow-ups or notifications."
)


LOG_FILE = "actions.log"                   # the permanent record

def log_action(name, raw_args, result):
    status = "refused" if "error" in result else "done"
    entry = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "tool": name,
        "args": raw_args,
        "status": status,
        "result": result,
    }
    with open(LOG_FILE, "a") as f:         # "a" = append, never overwrite
        f.write(json.dumps(entry) + "\n")  # one event per line


def call_llm(messages):
    payload = {"model": MODEL, "messages": messages, "tools": TOOLS}
    r = httpx.post(URL, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]


def run_tool(name, raw_args):
    """Allow-list, parse, hard rules, human approval, then run. Never crash."""
    if name not in TOOL_FUNCTIONS:                     # gate 1: is it a real tool?
        return {"error": f"Unknown tool '{name}'. Available: {list(TOOL_FUNCTIONS)}"}
    try:
        args = json.loads(raw_args)                    # gate 2: valid JSON?
    except json.JSONDecodeError:
        return {"error": "Arguments were not valid JSON"}
    try:
        if name in PRECHECKS:                          # gate 3: hard rules, in code
            problem = PRECHECKS[name](**args)
            if problem:
                return {"error": problem}
        if name in NEEDS_APPROVAL:                     # gate 4: human in the loop
            print(f"\n*** APPROVAL NEEDED: {name} {args}")
            answer = input("Approve? (yes/no): ").strip().lower()
            if answer != "yes":
                return {"error": "A human declined this action. Do not retry it."}
        return TOOL_FUNCTIONS[name](**args)            # all gates passed: run it
    except TypeError as e:                             # wrong or missing arguments
        return {"error": f"Bad arguments: {e}"}
    except Exception as e:                             # the tool itself failed
        return {"error": f"Tool failed: {e}"}


def run_agent(goal):
    actions_done = []                          # notebook of changes that really happened
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": goal},
    ]
    for step in range(1, MAX_STEPS + 1):       # the loop, with a cap
        reply = call_llm(messages)             # THINK

        if not reply.get("tool_calls"):        # no tool asked: model is done
            return reply["content"]

        messages.append({"role": "assistant", "content": None,
                         "tool_calls": reply["tool_calls"]})

        for call in reply["tool_calls"]:       # ACT
            name = call["function"]["name"]
            raw_args = call["function"]["arguments"]
            result = run_tool(name, raw_args)
            print(f"[step {step}] {name}({raw_args}) -> {result}")   # our trace
            if name in WRITE_TOOLS:                              # a change was attempted
                log_action(name, raw_args, result)               # record it, success or not
                if "error" not in result:                        # it really happened
                    actions_done.append(f"{name}({raw_args}) -> {result}")

            messages.append({                  # OBSERVE
                "role": "tool",
                "tool_call_id": call["id"],
                "content": json.dumps(result),
            })

    if actions_done:                       # the cap hit, but some changes already happened
        done = "; ".join(actions_done)
        return ("Stopped: step limit reached. "
                f"Already done: {done}. Nothing else was changed.")
    return "Stopped: step limit reached. No changes were made."


if __name__ == "__main__":
    goal = input("You: ")
    print("AGENT:", run_agent(goal))