import cv2

def preprocess_for_ocr(img):
    """
    Prepare the image crop for Tesseract OCR.
    """
    if img is None or img.size == 0:
        return None
    
    # 1. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Resize to make the text larger (helps OCR)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # 3. Apply thresholding (turns image black and white)
    # Using Otsu's thresholding to handle different lighting automatically
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh