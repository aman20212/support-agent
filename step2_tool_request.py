import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

URL = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
    "Content-Type": "application/json",
}

# The tool list: we only DESCRIBE the tool. No real function exists yet.
tools = [
    {
        "type": "function",
        "function": {
            "name": "look_up_order",
            "description": "Get the details of one customer order (item, amount, "
                           "status, delivery date) using its order id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order id, for example 1002",
                    }
                },
                "required": ["order_id"],
            },
        },
    }
]

payload = {
    "model": "openai/gpt-oss-20b",
    "messages": [
        {"role": "user", "content": "What is the status of order 1002?"}
    ],
    "tools": tools,            # NEW: tell the model which tools exist
}

response = httpx.post(URL, headers=headers, json=payload, timeout=30)
response.raise_for_status()

message = response.json()["choices"][0]["message"]
print(json.dumps(message, indent=2))     # show the whole reply, nicely formatted