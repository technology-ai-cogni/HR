import os
from dotenv import load_dotenv
import openai

def test_openai_connection():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or "your_openai_api_key_here" in api_key:
        print("Error: OPENAI_API_KEY is not set in .env file.")
        print("Please edit the .env file in this directory and replace 'your_openai_api_key_here' with your actual OpenAI API Key.")
        return

    model = os.getenv("OPENAI_MODEL", os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"))
    print(f"Testing OpenAI connection using model '{model}'...")
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say hello!"}
            ],
            temperature=0.0
        )
        print("\nSuccess! OpenAI response:")
        print(response.choices[0].message.content.strip())
    except Exception as e:
        print("\nError connecting to OpenAI API:")
        print(e)

if __name__ == "__main__":
    test_openai_connection()
