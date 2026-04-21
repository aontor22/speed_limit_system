# Libraries

import threading
import time
import cv2
import numpy as np
import shutil
import re
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.detector import UniversalDetector
from src.recognizer import SpeedRecognizer
from src.utils import preprocess_for_ocr
from src.database import init_db, save_violation, get_recent_violations

# --- SYSTEM CONFIGURATION ---
SYSTEM_CONFIG = {
    "mode": "webcam",
    "source_path": None,
    "new_input_ready": False
}

# ✅ FIX 1: initialize global variable
violation_in_progress = False

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

stop_event = threading.Event()

# --- SHARED STATE ---
traffic_data = {
    "current_speed": 0,
    "speed_limit": 0,
    "status": "Safe",
    "fps": 0,
    "violation_detected": False,
    "timestamp": ""
}

# --- ML MODELS ---
detector = UniversalDetector(sign_model_path="models/speed_limit_yolo.pt")
recognizer = SpeedRecognizer()

# --- HELPER FUNCTION ---
def process_single_frame(frame):
    detected_limit = 0
    sign_results = detector.detect_signs(frame)

    print("DETECTIONS:", len(sign_results))  # DEBUG

    for r in sign_results:
        for box in r.boxes:
            print("BOX FOUND")  # DEBUG

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            sign_crop = frame[y1:y2, x1:x2]

            # Save debug crop
            cv2.imwrite("debug_crop.jpg", sign_crop)

            processed_crop = preprocess_for_ocr(sign_crop)

            if processed_crop is not None:
                speed_text = recognizer.extract_speed(processed_crop)

                if speed_text is not None:
                    speed_text = str(speed_text)
                    print("OCR RAW:", speed_text)

                    digits = re.findall(r'\d+', speed_text)
                    if digits:
                        detected_limit = int(digits[0])

    return detected_limit


# --- MAIN PROCESS ENGINE ---
def process_engine(frame, detector, recognizer):
    global traffic_data, violation_in_progress

    try:
        limit = process_single_frame(frame)
        current_speed = 75

        print(f"DEBUG → Speed: {current_speed}, Limit: {limit}")

        is_violation = (limit > 0 and current_speed > limit)

        # --- DB LOGIC ---
        if is_violation:
            if not violation_in_progress:
                print("NEW VIOLATION → Saving to DB")
                save_violation(speed=current_speed, limit=limit)
                violation_in_progress = True
        else:
            violation_in_progress = False

        # --- Update state ---
        traffic_data["current_speed"] = current_speed
        traffic_data["speed_limit"] = limit
        traffic_data["status"] = "Violation" if is_violation else "Safe"
        traffic_data["timestamp"] = time.strftime("%H:%M:%S")

    except Exception as e:
        print("AI ERROR:", e)

    return frame


# --- AI THREAD ---
def run_ai_logic():
    global SYSTEM_CONFIG

    while not stop_event.is_set():
        mode = SYSTEM_CONFIG["mode"]
        source = SYSTEM_CONFIG["source_path"]

        # Webcam handled in frontend
        if mode == "webcam":
            time.sleep(0.1)
            continue

        # VIDEO MODE
        if mode == "video" and source:
            cap = cv2.VideoCapture(source)
            print("AI Thread: Starting video...")

            while not stop_event.is_set() and not SYSTEM_CONFIG["new_input_ready"]:
                success, frame = cap.read()
                if not success:
                    break

                process_engine(frame, detector, recognizer)

            cap.release()

        # IMAGE MODE
        elif mode == "image" and source:
            print(f"AI Thread: Processing image: {source}")
            frame = cv2.imread(source)

            if frame is not None:
                process_engine(frame, detector, recognizer)
            else:
                print("Failed to read image")

            # ✅ FIX 2: STOP LOOPING
            SYSTEM_CONFIG["mode"] = "idle"
            SYSTEM_CONFIG["source_path"] = None
            SYSTEM_CONFIG["new_input_ready"] = False

        time.sleep(0.1)


# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    print("Cleaned uploads")

    init_db()

    thread = threading.Thread(target=run_ai_logic, daemon=True)
    thread.start()
    print("AI Thread started")

    yield

    stop_event.set()
    print("Shutting down...")


# --- APP ---
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://speed-limit-system.onrender.com",
        "https://speed-limit-system.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- ROUTES ---
@app.get("/")
def root():
    return {"message": "Speed Detection API running"}


@app.get("/api/history")
async def get_history():
    return get_recent_violations(limit=10)


@app.get("/api/data")
async def get_data():
    return traffic_data


@app.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    SYSTEM_CONFIG["mode"] = "image"
    SYSTEM_CONFIG["source_path"] = file_path
    SYSTEM_CONFIG["new_input_ready"] = True

    return {"message": "Image uploaded"}


@app.post("/api/process-frame")
async def process_frame(file: UploadFile = File(...)):
    contents = await file.read()

    np_arr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid frame")

    limit = process_single_frame(frame)
    current_speed = 75

    status = "Violation" if (limit > 0 and current_speed > limit) else "Safe"

    return {
        "current_speed": current_speed,
        "speed_limit": limit,
        "status": status,
        "timestamp": time.strftime("%H:%M:%S")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
