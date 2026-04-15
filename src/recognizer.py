import pytesseract
import cv2
from collections import deque

class SpeedRecognizer:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        self.history = deque(maxlen=5)

        # Real-world valid speeds
        self.valid_speeds = [20, 30, 40, 50, 60, 70, 80, 90, 100, 120]

    def preprocess(self, img):
        if img is None or img.size == 0:
            return None

        # Handle grayscale or color
        if len(img.shape) == 2:
            gray = img
        else:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Resize (boost OCR accuracy)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # Blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Threshold
        thresh = cv2.threshold(
            blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]

        return thresh

    def validate_speed(self, value):
        if value is None:
            return None

        closest = min(self.valid_speeds, key=lambda x: abs(x - value))

        if abs(closest - value) <= 10:
            return closest

        return None

    def smooth_speed(self, value):
        if value:
            self.history.append(value)

        if len(self.history) == 0:
            return None

        return max(set(self.history), key=self.history.count)

    def extract_speed(self, cropped_img):
        try:
            processed = self.preprocess(cropped_img)

            if processed is None:
                return None

            config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
            text = pytesseract.image_to_string(processed, config=config)

            digits = ''.join(filter(str.isdigit, text))

            if digits == "":
                return None

            value = int(digits)

            valid_value = self.validate_speed(value)
            final_value = self.smooth_speed(valid_value)

            return final_value

        except Exception as e:
            print(f"OCR Error: {e}")
            return None