# Orders & Refunds Support Agent

A small AI agent that looks up orders, checks refund rules, opens tickets and
issues refunds, with safety checks in code in front of every action that changes money.
Built from scratch with plain HTTP calls to Groq, with no agent framework.

## How it works

- The model decides the next step. My code runs the tool. The result goes back to the model.
- This is the think, act, observe loop, capped at `MAX_STEPS = 6`.
- If the cap is hit, the agent reports any changes it had already made.
- The model requests, my code validates and runs.

## The four gates

Every tool call passes through `run_tool` before anything runs:

1. **Allow-list:** the tool name must exist in `TOOL_FUNCTIONS`.
2. **Valid JSON:** the arguments must parse.
3. **Hard rules in code:** `refund_precheck` checks that the order is eligible, the amount is valid, and the order was not already refunded.
4. **Human approval:** only an exact "yes" passes. Anything else is a no.

`issue_refund` also re-checks the rules itself, so it stays safe even if called directly.
Errors come back to the model as data, not as crashes.

## What I tested

Asking the agent in plain words to ignore the rules proved little, because the model
declined by itself. So `test_gates.py` calls `run_tool` directly with bad requests:

| Test | Caught by |
|---|---|
| Unknown tool `delete_all_orders` | Gate 1 |
| Arguments that are not valid JSON | Gate 2 |
| Wrong argument names | TypeError catch, returned as an error |
| Refund on order 1004 (delivered 19 days ago) | Gate 3 |
| Amount 99999 | Gate 3 |
| Valid refund of 500 | Gate 4 asks for approval, then runs |

## Action log and the step cap

- Every attempt to create a ticket or issue a refund is written to `actions.log`
  (one JSON line each, with time, tool, arguments, status and result).
  Refused attempts are logged too.
- If `MAX_STEPS` is reached after a change has already happened, the final message
  lists what was done, for example the ticket and the refund. If nothing was changed,
  it says so.

## Known gaps

- No ownership check: anyone can ask about any order.
- `TICKETS` and `REFUNDS` live in memory and reset on every run. The action log keeps the history.
- Approval is a terminal prompt, not a queue with a real identity.
- The model sometimes invents small promises, such as "our team will review it shortly".
- The action log is a plain file. It is not tamper-proof.

## Project files

- `agent.py`: the loop, the four gates, the system prompt and the action log
- `agent_tools.py`: the tools, fake order data and the rules
- `test_gates.py`: tests that call the gates directly

## How to run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# create a .env file containing: GROQ_API_KEY=your_key
python agent.py
```

Uses the Groq free tier with the `openai/gpt-oss-20b` model.