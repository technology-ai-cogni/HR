import requests
import json
from requests.exceptions import JSONDecodeError, ConnectionError

def test_lmstudio_chat_connection():
    endpoint = "http://localhost:1234/v1/chat/completions"
    payload = {
        "model": "deepseek-r1-distill-qwen-7b",  # update model as needed
        "messages": [
            { "role": "system", "content": "Always answer in rhymes. Today is Thursday" },
            { "role": "user", "content": "What day is it today?" }
        ],
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }
    print("Testing LMStudio chat endpoint connection...")
    try:
        response = requests.post(endpoint, json=payload)
        print("Status Code:", response.status_code)
        if response.status_code != 200:
            print("Error (non-200 response):", response.text)
        else:
            try:
                data = response.json()
                print("LMStudio Chat Response:", json.dumps(data, indent=2))
            except JSONDecodeError:
                print("Invalid JSON response:", response.text)
    except ConnectionError:
        print("LMStudio server is unavailable. Please ensure it's running.")

if __name__ == "__main__":
    test_lmstudio_chat_connection()
