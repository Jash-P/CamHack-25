import os
import json
import sys
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    print("Please run: pip install openai pydantic")
    sys.exit(1)

# --- SSL FIX (optional) ---
try:
    import certifi
    ca = certifi.where()
    os.environ["SSL_CERT_FILE"] = ca
    os.environ["REQUESTS_CA_BUNDLE"] = ca
except Exception:
    pass

# ---------- Schema ----------
class Dish(BaseModel):
    name: str
    restaurant: str

# ---------- Ingredients String ----------
ingredients = "Bread, Chicken"  # <-- put your ingredients here

# ---------- System Prompt ----------
SYSTEM_PROMPT = """You convert Minecraft chest or furnace food items into a real-world food order.

Rules:
1. Interpret Minecraft items into real dishes.
2. Return ONLY JSON (no text).
3. The JSON file should have the name of the dish and the restaurant to get it from.
The example JSON file looks like this:
{
  "name": "food",
  "restaurant": "store"
}


"""

# ---------- Call OpenAI ----------
def call_model(messages):
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0.2,
        messages=messages
    )
    return resp.choices[0].message.content

# ---------- Main ----------
def main():
    # Build system + user messages
    user_msg = f"Use these Minecraft items and output the final order only:\n\n{ingredients}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg}
    ]

    # Call ChatGPT
    output = call_model(messages)

    # Validate JSON with Pydantic
    try:
        parsed = Dish(**json.loads(output))
    except (ValidationError, json.JSONDecodeError):
        print("❌ Model returned invalid JSON. Output below:\n", output)
        return

    # Save validated JSON
    output_file = "dish_suggestion.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(parsed.model_dump(), f, indent=2)

    print(f"✅ Wrote {output_file}")
    print(parsed.model_dump())

if __name__ == "__main__":
    main()
