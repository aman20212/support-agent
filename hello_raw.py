import os
import httpx                                   # already installed with the groq package
from dotenv import load_dotenv

load_dotenv()                                  # read the key from .env

URL = "https://api.groq.com/openai/v1/chat/completions"   # the address

headers = {                                    # your ID card
    "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
    "Content-Type": "application/json",
}

payload = {                                    # the order form
    "model": "openai/gpt-oss-20b",
    "messages": [
        {"role": "user", "content": "Explain what an LLM is, in one sentence."}
    ],
}

response = httpx.post(URL, headers=headers, json=payload, timeout=30)
response.raise_for_status()                    # stop with a clear error if not 200

data = response.json()                         # the whole reply, as a dictionary
print(data["choices"][0]["message"]["content"])