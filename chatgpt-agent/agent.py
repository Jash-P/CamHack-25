import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat():
    print("🤖 ChatGPT Agent (type 'exit' to quit)\n")

    # Conversation history
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

    while True:
        user_input = input("You: ")

        if user_input.lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break

        # Add user message
        messages.append({"role": "user", "content": user_input})

        try:
            # Send request to ChatGPT
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # or "gpt-4o" / "gpt-3.5-turbo"
                messages=messages
            )

            # Get reply
            reply = response.choices[0].message.content
            print(f"GPT: {reply}\n")

            # Add assistant reply to history
            messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            print("⚠️ Error:", e)
            break

if __name__ == "__main__":
    chat()
