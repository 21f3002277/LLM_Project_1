import os
import requests

def call_llm(prompt: str) -> str:
    url = "https://api.aiproxy.io/v1/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['AIPROXY_TOKEN']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "prompt": prompt,
        "max_tokens": 100
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"LLM API error: {response.text}")
    return response.json()["choices"][0]["text"]