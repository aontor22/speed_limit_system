import cv2
import pytesseract
from ultralytics import YOLO

class TrafficEngine:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.conf_threshold = 0.5

    def process_frame(self, frame):
        """
        Input: OpenCV BGR Frame
        Output: { 'limit': int, 'detected': bool, 'annotated_frame': ndarray }
        """
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        detected_limit = 0
        is_detected = False

        for r in results:
            for box in r.boxes:
                is_detected = True
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # OCR Logic
                crop = frame[y1:y2, x1:x2]
                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                
                config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
                text = pytesseract.image_to_string(thresh, config=config).strip()
                
                if text.isdigit():
                    detected_limit = int(text)
                
                # Draw on frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{detected_limit} km/h", (x1, y1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        return {
            "limit": detected_limit,
            "detected": is_detected,
            "frame": frame
        }