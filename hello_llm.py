import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()                                   # reads .env into environment
client = Groq(api_key=os.environ["GROQ_API_KEY"])

MODEL = "llama-3.3-70b-versatile"               # check this name in the Groq console

reply = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "Say hello in five words."}],
)
print(reply.choices[0].message.content)