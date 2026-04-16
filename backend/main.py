from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cv2
import threading
from backend.src.engine import TrafficAI
import time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Global Controller
ai = TrafficAI("models/speed_limit_yolo.pt")
cap = cv2.VideoCapture(0) # Use 0 for webcam or "path/to/video.mp4"

# Shared Data
state = {
    "my_speed": 75,
    "limit": 0,
    "status": "Safe",
    "fps": 0
}

def generate_frames():
    prev_time = 0
    while True:
        success, frame = cap.read()
        if not success: break
        
        # Calculate FPS
        curr_time = time.time()
        state["fps"] = round(1 / (curr_time - prev_time), 1)
        prev_time = curr_time

        # Process
        annotated_frame, limit, status, _ = ai.process_frame(frame, state["my_speed"])
        state["limit"] = limit
        state["status"] = status

        # Encode for Streaming
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/data")
def get_data():
    return state

@app.post("/api/set_speed/{speed}")
def set_speed(speed: int):
    state["my_speed"] = speed
    return {"msg": "Speed Updated"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)