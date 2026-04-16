import csv
import os
from datetime import datetime

class SpeedLogger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.log_file = os.path.join(self.log_dir, "detection_history.csv")
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # Create file with headers if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Detected_Speed_Limit"])

    def log(self, speed_value):
        """
        Appends a detection to the CSV file.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, speed_value])
            print(f"Logged: {speed_value} at {timestamp}")
        except Exception as e:
            print(f"Logging Error: {e}")