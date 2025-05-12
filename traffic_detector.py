from ultralytics import YOLO
import torch
import cv2
import numpy as np
import paho.mqtt.client as mqtt
import ssl 

# MQTT Configuration
BROKER = "192.168.223.33"  # Replace with your PC's local IP
PORT = 8883
TOPIC_LIGHT = "traffic/light"
TOPIC_COUNT = "traffic/vehicle_count"
TOPIC_GREEN_TIME = "traffic/green_time"  # New MQTT topic for green time

# Initialize MQTT
client = mqtt.Client()
client.tls_set(ca_certs=r'C:\Users\asdcy\Downloads\ca.crt', tls_version=ssl.PROTOCOL_TLS)
client.connect(BROKER, PORT, 60)

# Set device (Use GPU if available, else CPU)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load YOLOv8 model
model = YOLO("yolov8n.pt").to(device)

# Open pre-recorded video
cap = cv2.VideoCapture("C:/Users/asdcy/Downloads/vecteezy_moving-cars-on-the-motorway-during-sunset-busy-traffic-on-a_11389863.mov")

# Frame dimensions
frame_width, frame_height = 640, 480

# Default traffic light timing
base_green_time = 20  # Default green light time in seconds
max_green_time = 60   # Maximum allowed green light time
min_green_time = 10   # Minimum green light time

previous_traffic = 0  # Stores last frame's traffic count
frame_count = 0  # To track frames

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (frame_width, frame_height))

    # Run YOLO vehicle detection
    results = model(frame, device=device)  
    vehicle_count = len(results[0].boxes)  # Count detected vehicles

    # Adjust green light duration dynamically
    if vehicle_count > previous_traffic:  
        green_time = min(base_green_time + (vehicle_count * 2), max_green_time)  
    else:
        green_time = max(base_green_time - (vehicle_count * 2), min_green_time)  

    # Store for next iteration
    previous_traffic = vehicle_count  

    # Determine traffic light status
    if vehicle_count > 5:
        light_status = "RED"
        client.publish(TOPIC_LIGHT, "red")  # Send "red" signal to ESP32
    else:
        light_status = "GREEN"
        client.publish(TOPIC_LIGHT, "green")  # Send "green" signal to ESP32

    # Send traffic data via MQTT
    client.publish(TOPIC_COUNT, str(vehicle_count))  # Send vehicle count
    client.publish(TOPIC_GREEN_TIME, str(green_time))  # Send green time (NEW)

    # Draw bounding boxes
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green box

    # Display vehicle count and green light time
    cv2.putText(frame, f"Vehicles: {vehicle_count}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.putText(frame, f"Green Time: {green_time}s", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv2.putText(frame, f"Light: {light_status}", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if light_status == "GREEN" else (0, 0, 255), 2)

    # Draw a traffic light indicator
    traffic_light = np.zeros((150, 80, 3), dtype=np.uint8)  # Small black box for light

    if vehicle_count > 5:
        cv2.circle(traffic_light, (40, 40), 20, (0, 0, 255), -1)  # Red light (high traffic)
        traffic_status = "RED - Heavy Traffic"
    else:
        cv2.circle(traffic_light, (40, 110), 20, (0, 255, 0), -1)  # Green light (low traffic)
        traffic_status = "GREEN - Normal Flow"

    # Place traffic light in top-right corner
    frame[10:160, 550:630] = traffic_light

    # Show traffic light status
    cv2.putText(frame, traffic_status, (400, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Save a sample output image
    if frame_count == 50:  # Save after 50 frames
        cv2.imwrite("output_visual.jpg", frame)
        print("Sample output image saved as 'output_visual.jpg'")

    frame_count += 1

    # Show final output with visuals
    cv2.imshow("Traffic Detection with Traffic Light", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' to exit
        break

cap.release()
cv2.destroyAllWindows()
client.disconnect()
