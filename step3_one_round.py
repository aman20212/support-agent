import os
import json
import httpx
from dotenv import load_dotenv
from agent_tools import TOOLS, TOOL_FUNCTIONS

load_dotenv()
URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
    "Content-Type": "application/json",
}
MODEL = "openai/gpt-oss-20b"


def call_llm(messages):                      # one trip to the model
    payload = {"model": MODEL, "messages": messages, "tools": TOOLS}
    r = httpx.post(URL, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]


messages = [{"role": "user", "content": "What is the status of order 1002?"}]

reply = call_llm(messages)                   # THINK: the model decides

if not reply.get("tool_calls"):              # no tool asked: this is the answer
    print("FINAL:", reply["content"])
else:
    # keep the model's request in the conversation
    messages.append({"role": "assistant", "content": None, "tool_calls": reply["tool_calls"]})

    for call in reply["tool_calls"]:
        name = call["function"]["name"]                      # which tool
        args = json.loads(call["function"]["arguments"])     # string -> dictionary
        print("MODEL ASKED FOR:", name, args)

        result = TOOL_FUNCTIONS[name](**args)                # ACT: YOUR code runs it
        print("MY CODE RAN IT, RESULT:", result)

        messages.append({                                    # OBSERVE: hand it back
            "role": "tool",
            "tool_call_id": call["id"],                      # which request this answers
            "content": json.dumps(result),
        })

    final = call_llm(messages)                               # model reads the result
    print("FINAL:", final["content"])