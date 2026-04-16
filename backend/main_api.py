import threading
import time
import cv2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.detector import UniversalDetector
from src.recognizer import SpeedRecognizer
from src.utils import preprocess_for_ocr

# --- API CONFIGURATION ---
app = FastAPI()

# Enable CORS so React (port 3000) can talk to FastAPI (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL STATE ---
# This dictionary stores the latest AI results to be picked up by the API
traffic_data = {
    "current_speed": 75,
    "speed_limit": 0,
    "status": "Safe",
    "fps": 0,
    "violation_detected": False,
    "timestamp": ""
}

# --- AI PROCESSING THREAD ---
def run_ai_logic():
    global traffic_data
    
    # Initialize your previous logic
    detector = UniversalDetector(sign_model_path="models/speed_limit_yolo.pt")
    recognizer = SpeedRecognizer()
    cap = cv2.VideoCapture(0) # or "data/test_video.mp4"
    
    prev_time = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success: break

        # cv2.imshow("Detection Feed", frame)

        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

        # Calculate FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time)
        prev_time = curr_time

        # Run Detection
        sign_results = detector.detect_signs(frame)
        
        current_limit = traffic_data["speed_limit"]
        
        for r in sign_results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                sign_crop = frame[y1:y2, x1:x2]
                processed_crop = preprocess_for_ocr(sign_crop)
                
                if processed_crop is not None:
                    speed_text = recognizer.extract_speed(processed_crop)
                    if speed_text.isdigit():
                        current_limit = int(speed_text)

        # Update Global State
        traffic_data["speed_limit"] = current_limit
        traffic_data["fps"] = round(fps, 1)
        
        # Check Violation
        if current_limit > 0 and traffic_data["current_speed"] > current_limit:
            traffic_data["status"] = "Violation"
            traffic_data["violation_detected"] = True
        else:
            traffic_data["status"] = "Safe"
            traffic_data["violation_detected"] = False
            
        traffic_data["timestamp"] = time.strftime("%H:%M:%S")

        # Small delay to prevent CPU saturation
        time.sleep(0.01)

# Start the AI in a background thread
ai_thread = threading.Thread(target=run_ai_logic, daemon=True)
ai_thread.start()

# --- API ENDPOINTS ---

@app.get("/api/data")
async def get_traffic_data():
    """
    Returns the latest state of the AI detection system.
    Called by React every 500ms.
    """
    return traffic_data

@app.get("/")
def read_root():
    return {"message": "Traffic System API is Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)