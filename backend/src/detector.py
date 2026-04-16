from ultralytics import YOLO

class UniversalDetector:
    def __init__(self, sign_model_path, vehicle_model_path="yolov8n.pt"):
        # Your custom model for signs
        self.sign_model = YOLO(sign_model_path)
        # Pretrained model for vehicles (Class IDs: 2:car, 3:motorcycle, 5:bus, 7:truck)
        self.vehicle_model = YOLO(vehicle_model_path)
        
    def detect_signs(self, frame):
        # We use .track() instead of .predict() to keep IDs for signs
        return self.sign_model.track(frame, persist=True, conf=0.5, verbose=False)

    def detect_vehicles(self, frame):
        # Only detect cars, motorcycles, buses, and trucks (COCO classes)
        return self.vehicle_model.track(frame, persist=True, classes=[2, 3, 5, 7], verbose=False)