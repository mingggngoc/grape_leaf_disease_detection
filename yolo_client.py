import time
import datetime
import requests
import cv2
from ultralytics import YOLO

# --- CONFIGURATION ---
MODEL_PATH = "best.pt"
UPDATE_URL = "http://127.0.0.1:5000/update"
CHECK_URL = "http://127.0.0.1:5000/check_trigger"
INTERVAL_HOURS = 1
# ---------------------

model = YOLO(MODEL_PATH)

def capture_and_send():
    print(f"[{datetime.datetime.now()}] Initializing YOLO inference...")
    
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Error: Webcam access failed.")
        return

    results = model(frame)
    result = results[0]
    
    detected_class = "Nothing detected"
    
    # 1. Handle Classification Models (-cls)
    if hasattr(result, 'probs') and result.probs is not None:
        # Get the index of the class with the highest probability
        top1_idx = int(result.probs.top1)
        detected_class = model.names[top1_idx]
        
    # 2. Handle Object Detection Models (Standard)
    elif hasattr(result, 'boxes') and result.boxes is not None:
        if len(result.boxes) > 0:
            cls_id = int(result.boxes[0].cls[0])
            detected_class = model.names[cls_id]

    # Save the plotted image (works seamlessly for both tasks)
    temp_img_path = "temp_detection.jpg"
    annotated_frame = result.plot()
    cv2.imwrite(temp_img_path, annotated_frame)

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {"class_name": detected_class, "timestamp": now_str}
    
    try:
        with open(temp_img_path, 'rb') as img_file:
            files = {'image': img_file}
            response = requests.post(UPDATE_URL, data=payload, files=files)
        if response.status_code == 200:
            print(f"Update successful. Class: {detected_class}")
        else:
            print(f"Server Error: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Network Error: Verification failed. Is app.py up?")

def main():
    # Run once right away on initial execution
    capture_and_send()
    
    seconds_in_hour = INTERVAL_HOURS * 3600
    last_scheduled_time = time.time()
    
    print("YOLO background daemon running. Listening for manual triggers...")
    try:
        while True:
            current_time = time.time()
            
            # 1. Check if an hour has elapsed since last scheduled capture
            if current_time - last_scheduled_time >= seconds_in_hour:
                print("Scheduled hourly trigger fired.")
                capture_and_send()
                last_scheduled_time = current_time
            
            # 2. Poll server for a web UI manual trigger request
            try:
                response = requests.get(CHECK_URL, timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("trigger_requested", False):
                        print("Manual 'Take Picture' trigger detected from UI!")
                        capture_and_send()
                        # Update the schedule marker so you don't double-capture close together if preferred
                        last_scheduled_time = time.time() 
            except requests.exceptions.ConnectionError:
                # Silently catch brief server restarts
                pass

            # Check again for UI interactions every second
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nDaemon terminated clean.")

if __name__ == "__main__":
    main()