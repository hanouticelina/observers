import os

from observers.observers import wrap_openai
from openai import OpenAI

openai_client = OpenAI(
    base_url="https://api-inference.huggingface.co/v1/", api_key=os.getenv("HF_TOKEN")
)

client = wrap_openai(openai_client)

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-Coder-32B-Instruct",
    messages=[{"role": "user", "content": "Tell me a joke."}],
)
