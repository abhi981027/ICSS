from flask import Flask, request, render_template, jsonify
import logging
import requests
import random
import time

app = Flask(__name__)

# Configure logging to track hacker activity
logging.basicConfig(filename="honeypot.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Fake traffic light status (default is "Red")
current_light = "Red"
last_manual_change = 0  # Timestamp to track manual override

# Function to generate fake traffic data
def generate_fake_data():
    return {
        "traffic_status": random.choice(["Heavy Traffic", "Moderate Traffic", "Light Traffic"]),
        "light_status": current_light,
        "vehicle_count": random.randint(10, 200),
        "green_time": random.randint(15, 30),
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# Function to get hacker IP details
def get_attacker_info(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        return response.json()
    except:
        return {"error": "Geo lookup failed"}

@app.route("/")
def index():
    attacker_ip = request.remote_addr
    attacker_info = get_attacker_info(attacker_ip)

    # Log hacker visits
    logging.info(f"[VISIT] IP: {attacker_ip}, User-Agent: {request.headers.get('User-Agent')}, Location: {attacker_info}")

    return render_template("index.html")

@app.route("/api", methods=["GET"])
def fake_api():
    attacker_ip = request.remote_addr
    attacker_info = get_attacker_info(attacker_ip)

    # Generate fake traffic data
    fake_data = generate_fake_data()

    # Log hacker API requests
    logging.info(f"[API REQUEST] IP: {attacker_ip}, Data: {request.data}, Headers: {dict(request.headers)}, Location: {attacker_info}")

    return jsonify(fake_data)

@app.route("/set-light", methods=["POST"])
def set_light():
    global current_light, last_manual_change
    attacker_ip = request.remote_addr
    attacker_info = get_attacker_info(attacker_ip)

    new_light = request.form.get("light", "Red")
    if new_light not in ["Red", "Green"]:
        return jsonify({"status": "error", "message": "Invalid light status"}), 400

    current_light = new_light
    last_manual_change = time.time()

    logging.info(f"[LIGHT CHANGE] IP: {attacker_ip}, Set Light: {new_light}, Location: {attacker_info}")

    return jsonify({"status": "success", "light_status": current_light})

@app.route("/toggle-light", methods=["GET"])
def toggle_light():
    global current_light, last_manual_change
    if time.time() - last_manual_change > 15:  # Auto-switch only if no manual change in last 15 sec
        current_light = "Green" if current_light == "Red" else "Red"
    return jsonify({"light_status": current_light})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
