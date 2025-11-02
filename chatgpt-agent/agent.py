import os
import json
import sys
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

# ---------- File path ----------
file_path = "dataset_ubereats-scraper_2025-11-02_12-37-53-368.json"

# ---------- Read JSON file ----------
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- Extract restaurants and menu items ----------
restaurant_names = []
menu_items = []  # List of dicts: [{"restaurant": ..., "items": [...]}]

for restaurant in data:
    name = restaurant.get("title", "Unknown Restaurant")
    restaurant_names.append(name)

    items = []
    for section in restaurant.get("menu", []):
        for item in section.get("catalogItems", []):
            title = item.get("title")
            if title:
                items.append(title)

    menu_items.append({"restaurant": name, "items": items})

print(restaurant_names)
print(restaurant_names.index("Cafe 121"))

# ---------- Print check ----------
print(f"Loaded {len(restaurant_names)} restaurants.")
print(f"Example restaurant: {restaurant_names[2]}")
print(f"Example menu items: {menu_items[2]}")

# ---------- OpenAI import check ----------
try:
    from openai import OpenAI
except ImportError:
    print("Please run: pip install openai pydantic python-dotenv")
    sys.exit(1)

# ---------- SSL FIX ----------
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

# ---------- Ingredients Example ----------
ingredients = "Bread, Chicken"  # <-- Replace dynamically later if needed

# ---------- Build SYSTEM PROMPT ----------
restaurant_list_str = ", ".join(restaurant_names)

menu_data_str = "\n".join([
    f"- {entry['restaurant']}: {', '.join(entry['items'][:20])}..."
    for entry in menu_items
])

SYSTEM_PROMPT = f"""
You are a food ordering assistant.

You must only select restaurants and dishes that exist in the provided data.

RULES:
1. You must choose one valid restaurant from this list:
   {restaurant_list_str}

2. You must choose one valid menu item from that restaurant's list below.
   Each restaurant's allowed dishes are listed here:
   {menu_data_str}
   The item outputted must be the exact name in the menu list. It cannot be abreviated.

3. The menu item must be available in that exact restaurant. The indexes of each restaurant_list corresponds to the index of the menu list.
4. Return ONLY valid JSON with this structure:
   {{
     "name": "menu item name",
     "restaurant": "restaurant name"
   }}

   THE NAME MUST BE THE LITERAL NAME OF AN ITEM IN THE MENU LIST OF THAT RESPECTIVE RESTAURANT
5. Do not invent, modify, or translate names — use exact matches from the list.
6. If no valid match exists, return an empty JSON object: {{}}
"""

# ---------- Call OpenAI ----------
def call_model(messages):
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        temperature=0.1,
        messages=messages
    )
    return resp.choices[0].message.content

# ---------- Main ----------
def main():
    user_msg = f"You have these Minecraft ingredients: {ingredients}. " \
               f"Suggest a matching real-world dish and restaurant ONLY from the valid dataset."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg}
    ]

    # Call model
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
