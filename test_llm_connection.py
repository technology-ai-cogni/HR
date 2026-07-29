import requests
from requests.exceptions import JSONDecodeError, ConnectionError

def test_llm_connection():
    test_prompt = "Hello, test!"
    # Note the endpoint now includes /api/generate
    endpoint = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": "llama3.2:3b-instruct-fp16",  # update the model name as needed
        "prompt": test_prompt,
        "stream": False
    }

    try:
        response = requests.post(endpoint, json=payload)
        print("Status Code:", response.status_code)
        if response.status_code != 200:
            print("Error (non-200 response):", response.text)
        else:
            try:
                data = response.json()
                print("LLM Response:", data)
            except JSONDecodeError:
                print("Invalid JSON response:", response.text)
    except ConnectionError:
        print("LLM server is unavailable. Please ensure it's running.")

if __name__ == "__main__":
    test_llm_connection()
