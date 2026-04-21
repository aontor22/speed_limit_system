import cv2
from backend.src.detector import UniversalDetector
from backend.src.recognizer import SpeedRecognizer
from backend.src.utils import preprocess_for_ocr

def main():
    # Setup
    detector = UniversalDetector(sign_model_path="models/speed_limit_yolo.pt")
    recognizer = SpeedRecognizer()
    cap = cv2.VideoCapture("data/test_video.mp4")

    # --- SIMULATION VARIABLES ---
    MY_CURRENT_SPEED = 75  # Simulated vehicle speed
    current_limit = None   # Use None instead of 0
    alert_mode = False
    # ----------------------------

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # 1. Detect Vehicles
        vehicle_results = detector.detect_vehicles(frame)

        # 2. Detect Signs
        sign_results = detector.detect_signs(frame)

        # Draw Vehicle Boxes (Blue)
        for r in vehicle_results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                obj_id = int(box.id[0]) if box.id is not None else 0

                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, f"Vehicle ID: {obj_id}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Draw Sign Boxes + OCR
        for r in sign_results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Safe crop
                sign_crop = frame[y1:y2, x1:x2]

                if sign_crop is None or sign_crop.size == 0:
                    continue

                # Preprocess
                processed_crop = preprocess_for_ocr(sign_crop)

                if processed_crop is not None:
                    speed_value = recognizer.extract_speed(processed_crop)

                    # ✅ FIX: no more isdigit()
                    if speed_value is not None:
                        current_limit = speed_value

                # Draw Sign Box (Green)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # 3. Violation Logic
        if current_limit is not None:
            if MY_CURRENT_SPEED > current_limit:
                alert_mode = True
                status_color = (0, 0, 255)  # Red
            else:
                alert_mode = False
                status_color = (0, 255, 0)  # Green
        else:
            status_color = (255, 255, 255)  # White

        # UI OVERLAY
        cv2.rectangle(frame, (0, 0), (320, 130), (0, 0, 0), -1)

        cv2.putText(frame, f"MY SPEED: {MY_CURRENT_SPEED} km/h", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        limit_text = f"{current_limit} km/h" if current_limit else "Detecting..."
        cv2.putText(frame, f"LIMIT: {limit_text}", (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        if alert_mode:
            cv2.putText(frame, "!!! OVER-SPEEDING !!!", (10, 105),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)

        cv2.imshow("Advanced ITS System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
