import requests
from requests.exceptions import JSONDecodeError, ConnectionError
import json

def test_lmstudio_connection():
    test_prompt = "Hello LMStudio test!"
    endpoint = "http://127.0.0.1:1234/api/generate"
    payload = {
        "model": "deepseek-r1-distill-qwen-7b",  # update model if needed
        "prompt": test_prompt,
        "stream": False
    }
    print("Testing LMStudio connection...")
    try:
        response = requests.post(endpoint, json=payload)
        print("Status Code:", response.status_code)
        if response.status_code != 200:
            print("Error (non-200 response):", response.text)
        else:
            try:
                data = response.json()
                print("LMStudio Response:", json.dumps(data, indent=2))
            except JSONDecodeError:
                print("Invalid JSON response:", response.text)
    except ConnectionError:
        print("LMStudio server is unavailable. Please ensure it's running.")

if __name__ == "__main__":
    test_lmstudio_connection()
