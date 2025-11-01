from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/chest', methods=['POST'])
def chest_data():
    data = request.get_json(force=True)  # parse JSON body
    print("📦 Received chest data:", data)

    # You can do whatever you want here — save to file, database, etc.
    # For example, just log the player and number of items:
    player = data.get('player')
    num_items = len(data.get('chestContents', []))
    print(f"🧍 Player {player} closed a chest with {num_items} items")

    # Respond back to Minecraft
    return jsonify({"status": "ok", "received": num_items})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)