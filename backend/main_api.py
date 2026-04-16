import threading
import time
import cv2
import numpy as np
import shutil
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.detector import UniversalDetector
from src.recognizer import SpeedRecognizer
from src.utils import preprocess_for_ocr

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML components once
detector = UniversalDetector(sign_model_path="models/speed_limit_yolo.pt")
recognizer = SpeedRecognizer()

# Shared state for real-time webcam
traffic_data = {
    "current_speed": 0,
    "speed_limit": 0,
    "status": "Safe",
    "fps": 0,
    "violation_detected": False,
    "timestamp": ""
}

# --- HELPER: LOGIC REUSE ---
def process_single_frame(frame):
    """
    Core logic to detect signs and OCR speed from a single OpenCV frame.
    Returns: (detected_limit, is_violation)
    """
    detected_limit = 0
    sign_results = detector.detect_signs(frame)
    
    for r in sign_results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            sign_crop = frame[y1:y2, x1:x2]
            processed_crop = preprocess_for_ocr(sign_crop)
            
            if processed_crop is not None:
                speed_text = recognizer.extract_speed(processed_crop)
                if speed_text.isdigit():
                    detected_limit = int(speed_text)
                    
    return detected_limit

# --- EXISTING REAL-TIME THREAD (Phase 1-5 legacy) ---
def run_ai_logic():
    global traffic_data
    cap = cv2.VideoCapture(0)
    prev_time = 0
    while cap.isOpened():
        success, frame = cap.read()
        if not success: break
        
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time)
        prev_time = curr_time

        # Reuse helper
        limit = process_single_frame(frame)
        
        # Update Global State (Simulated current speed for webcam)
        traffic_data["current_speed"] = 75 
        traffic_data["speed_limit"] = limit
        traffic_data["fps"] = round(fps, 1)
        traffic_data["status"] = "Violation" if (limit > 0 and 75 > limit) else "Safe"
        traffic_data["timestamp"] = time.strftime("%H:%M:%S")
        time.sleep(0.01)

threading.Thread(target=run_ai_logic, daemon=True).start()

# --- NEW: PHASE 1 ENDPOINTS ---

@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """
    Processes a single uploaded image.
    """
    # Read image file
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Run detection
    detected_limit = process_single_frame(frame)
    
    # Static test speed for the uploaded image result
    my_speed = 80 
    status = "Violation" if (detected_limit > 0 and my_speed > detected_limit) else "Safe"

    return {
        "detected_speed_limit": detected_limit,
        "your_speed": my_speed,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/api/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """
    Processes an uploaded video and returns a summary of detections.
    """
    # Save temporary file
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cap = cv2.VideoCapture(temp_path)
    max_limit_found = 0
    violations_count = 0
    frame_count = 0
    start_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        frame_count += 1
        # Process every 10th frame for speed in uploaded videos
        if frame_count % 10 == 0:
            limit = process_single_frame(frame)
            if limit > max_limit_found:
                max_limit_found = limit
            if limit > 0 and 80 > limit: # Assuming 80 is vehicle speed
                violations_count += 1

    cap.release()
    os.remove(temp_path) # Cleanup

    total_time = time.time() - start_time
    avg_fps = round(frame_count / total_time, 2) if total_time > 0 else 0

    return {
        "max_speed_limit_detected": max_limit_found,
        "total_violations_in_video": violations_count,
        "average_processing_fps": avg_fps,
        "frames_processed": frame_count
    }

@app.get("/api/data")
async def get_traffic_data():
    return traffic_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)