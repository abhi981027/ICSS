from flask import Flask, render_template, jsonify
from flask_mqtt import Mqtt
import threading
import ssl

# ADDED
from flask import request, redirect
from datetime import datetime

app = Flask(__name__)

# MQTT Configuration with TLS
app.config['MQTT_BROKER_URL'] = '192.168.223.33'  # Replace with your PC's local IP
app.config['MQTT_BROKER_PORT'] = 8883  # Changed to TLS port
app.config['MQTT_TLS_ENABLED'] = True
app.config['MQTT_TLS_CA_CERTS'] = r"C:\Users\asdcy\Downloads\mosquitto-certs\ca.crt"  # Path to CA certificate
app.config['MQTT_TLS_VERSION'] = ssl.PROTOCOL_TLS

mqtt = Mqtt(app)

# Store traffic data
traffic_status = {
    "vehicle_count": 0,
    "green_time": 20,
    "light_status": "GREEN"
}

#  ADDED: Hacker detection settings
TRUSTED_IPS = ['192.168.223.33']  # Your trusted IP
SUSPICIOUS_UA = ['curl', 'sqlmap', 'bot', 'scraper']
HONEYPOT_URL = 'http://192.168.223.33:8080/'  # Honeypot URL

#  ADDED: Hacker detection logic
@app.before_request
def detect_and_redirect_hacker():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '').lower()

    is_hacker = False

    if ip not in TRUSTED_IPS:
        is_hacker = True
    for bad_ua in SUSPICIOUS_UA:
        if bad_ua in user_agent:
            is_hacker = True

    if is_hacker:
        with open("hacker_log.txt", "a") as f:
            f.write(f"[{datetime.now()}] HACKER DETECTED: IP={ip}, UA={user_agent}\n")
        return redirect(HONEYPOT_URL, code=302)

# MQTT Message Handler (Updates traffic data from YOLO script)
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global traffic_status
    data = message.payload.decode()

    if message.topic == "traffic/light":
        traffic_status["light_status"] = "RED" if data == "red" else "GREEN"

    elif message.topic == "traffic/vehicle_count":
        if data.isnumeric():
            traffic_status["vehicle_count"] = int(data)

    elif message.topic == "traffic/green_time":  # NEW - Handle Green Time Updates
        if data.isnumeric():
            traffic_status["green_time"] = int(data)

# Subscribe to relevant MQTT topics on startup
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker")
    mqtt.subscribe("traffic/light")
    mqtt.subscribe("traffic/vehicle_count")
    mqtt.subscribe("traffic/green_time")  # NEW

# Route for main page
@app.route('/')
def index():
    return render_template('index.html', traffic=traffic_status)

# Route to get live traffic data
@app.route('/get-data')
def get_data():
    return jsonify(traffic_status)

# Route for manual light control
@app.route('/set-light/<color>')
def set_light(color):
    if color in ["red", "green"]:
        mqtt.publish('traffic/light', color)
    return "OK"

# Run Flask Server
def run_flask():
    # You can also add SSL/TLS to the Flask server if needed
    # app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False, ssl_context=('cert.pem', 'key.pem'))
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()