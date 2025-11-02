from flask import Flask, request, jsonify
import json, queue

app = Flask(__name__)
orders = queue.Queue()

@app.route("/api/chest", methods=["POST"])
def order():
    data = request.json
    print("Received order:", data)
    
    orders.put(data)
    print("Order queued")
    return {"status": "queued"}

@app.route("/api/order", methods=["GET"])
def next_order():
    if orders.empty():
        return {"status": "none"}
    return orders.get()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)