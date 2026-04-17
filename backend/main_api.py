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
from src.database import init_db, get_recent_violations, insert_violation 

# Initialize Database on script start
init_db()

# --- SYSTEM CONFIGURATION ---
# This allows us to switch modes dynamically
SYSTEM_CONFIG = {
    "mode": "webcam",        # "webcam", "video", or "image"
    "source_path": None,     # Path for uploaded video or image
    "new_input_ready": False # Flag to tell the thread to restart/refresh
}

# --- NEW: PHASE 2 ENDPOINTS ---
stop_event = threading.Event()


app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/history")
async def get_history():
    """
    Endpoint to fetch the last 10 violation records.
    Called by the React frontend to populate the history table.
    """
    history = get_recent_violations(limit=10)
    return history

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
    global traffic_data, SYSTEM_CONFIG
    
    detector = UniversalDetector(sign_model_path="models/speed_limit_yolo.pt")
    recognizer = SpeedRecognizer()
    window_name = "AI Pipeline - Speed Detection"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    while not stop_event.is_set():
        mode = SYSTEM_CONFIG["mode"]
        source = SYSTEM_CONFIG["source_path"] if mode != "webcam" else 0
        
        # --- BRANCH A: STREAM MODES (Webcam or Video) ---
        if mode in ["webcam", "video"]:
            cap = cv2.VideoCapture(source)
            print(f"AI Thread: Starting {mode} stream...")
            
            while not stop_event.is_set() and not SYSTEM_CONFIG["new_input_ready"]:
                success, frame = cap.read()
                if not success:
                    # If video ends, reset or loop
                    if mode == "video": break 
                    continue

                # Process Frame (Your existing YOLO + OCR logic)
                # annotated_frame, results = process_engine(frame, detector, recognizer)
                
                frame = process_engine(frame, detector, recognizer)
                cv2.imshow(window_name, frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_event.set()
                
            cap.release()

        # --- BRANCH B: STATIC MODE (Image) ---
        elif mode == "image" and source:
            print(f"AI Thread: Processing static image: {source}")
            frame = cv2.imread(source)
            if frame is not None:
                # Process Image Once
                # annotated_frame, results = process_engine(frame, detector, recognizer)
                
                frame = process_engine(frame, detector, recognizer)
                cv2.imshow(window_name, frame)
                cv2.waitKey(1000) # Show for 1 second minimum
            
            # Reset flag and wait for next input
            SYSTEM_CONFIG["new_input_ready"] = False

        # IDLE: Prevent the thread from consuming 100% CPU when waiting for input
        SYSTEM_CONFIG["new_input_ready"] = False
        time.sleep(0.1)

    cv2.destroyAllWindows()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    thread = threading.Thread(target=run_ai_logic, daemon=True)
    thread.start()
    print("AI Thread started.")

    yield

    # Shutdown
    stop_event.set()
    print("Shutting down AI thread...")

app = FastAPI(lifespan=lifespan)

def process_engine(frame, detector, recognizer):
    global traffic_data

    # Use your existing logic
    limit = process_single_frame(frame)

    current_speed = 75  # simulated

    # Update global state
    traffic_data["current_speed"] = current_speed
    traffic_data["speed_limit"] = limit
    traffic_data["status"] = "Violation" if (limit > 0 and current_speed > limit) else "Safe"
    traffic_data["timestamp"] = time.strftime("%H:%M:%S")

    return frame  # return for display

@app.get("/")
def root():
    return {"message": "Speed Detection API is running"}

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