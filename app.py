import os
import time
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'detections')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global states
latest_detection = {
    "class_name": "No data received yet",
    "timestamp": "N/A",
    "image_path": "/static/detections/latest.jpg"
}
trigger_requested = False  # Flags if the user clicked 'Take Picture'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YOLO Local Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; text-align: center; }
        .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .status-box { background: #eef2f7; padding: 15px; border-radius: 6px; margin: 20px 0; font-size: 1.2em; }
        .detection-image { max-width: 100%; height: auto; border-radius: 6px; margin-top: 15px; border: 1px solid #ddd; }
        .timestamp { color: #666; font-size: 0.9em; }
        .btn { background-color: #28a745; color: white; border: none; padding: 12px 24px; font-size: 1em; border-radius: 4px; cursor: pointer; transition: 0.2s; margin-bottom: 10px;}
        .btn:hover { background-color: #218838; }
        .btn:disabled { background-color: #6c757d; cursor: not-allowed; }
    </style>
    <script>
        function triggerCapture() {
            const btn = document.getElementById('capture-btn');
            btn.disabled = true;
            btn.innerText = "Capturing...";

            // Send trigger request to server
            fetch('/trigger', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    // Poll every 1 second to see if the client has fulfilled the request
                    let checks = 0;
                    const interval = setInterval(() => {
                        checks++;
                        fetch('/check_trigger')
                            .then(res => res.json())
                            .then(status => {
                                // If trigger_requested is false, it means client cleared it and uploaded new data
                                if (!status.trigger_requested || checks > 15) {
                                    clearInterval(interval);
                                    window.location.reload();
                                }
                            });
                    }, 1000);
                })
                .catch(err => {
                    alert("Error sending trigger request");
                    btn.disabled = false;
                    btn.innerText = "Take Picture Now";
                });
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>YOLO Detection Dashboard</h1>
        
        <button id="capture-btn" class="btn" onclick="triggerCapture()">Take Picture Now</button>

        <div class="status-box">
            <strong>Last Recorded Class:</strong> <span style="color: #007BFF;">{{ data.class_name }}</span>
            <p class="timestamp">Detected at: {{ data.timestamp }}</p>
        </div>
        <h3>Latest Image</h3>
        <img class="detection-image" src="{{ data.image_path }}?t={{ range(1, 99999) | random }}" alt="Latest YOLO Detection">
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, data=latest_detection)

# Endpoint for UI button to hit
@app.route('/trigger', methods=['POST'])
def trigger_action():
    global trigger_requested
    trigger_requested = True
    return jsonify({"status": "pending", "message": "Manual capture requested"})

# Endpoint for the YOLO client to poll
@app.route('/check_trigger', methods=['GET'])
def check_trigger():
    global trigger_requested
    return jsonify({"trigger_requested": trigger_requested})

@app.route('/update', methods=['POST'])
def update_detection():
    global latest_detection, trigger_requested
    
    if 'image' not in request.files or 'class_name' not in request.form:
        return jsonify({"error": "Missing data"}), 400
    
    file = request.files['image']
    class_name = request.form['class_name']
    timestamp = request.form.get('timestamp', 'Unknown Time')
    
    image_path = os.path.join(UPLOAD_FOLDER, 'latest.jpg')
    file.save(image_path)
    
    latest_detection['class_name'] = class_name
    latest_detection['timestamp'] = timestamp
    
    trigger_requested = False # Reset flag once data is successfully handled
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)