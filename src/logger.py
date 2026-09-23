import time
import csv
import os

LOG_FILE = os.path.join("logs", "flight_log.csv")

# Color constants
RED = '\033[31m'
GREEN = '\033[32m'
BLUE = '\033[34m'
YELLOW = '\033[33m'
RESET = '\033[0m' # Crucial to turn off the color

def init_logger(log_file=LOG_FILE):
    """Ensures logs directory exists and initializes CSV header."""
    os.makedirs("logs", exist_ok=True)
    with open(log_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Timestamp", "State", "Battery", "Height_cm", 
            "Pitch", "Roll", "Yaw", "Obstacle_Detected", "Detection_Value"
        ])

def log_telemetry(drone, state, detected, detection_val):
    """Appends current drone telemetry and detection metrics to CSV."""
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        battery = drone.get_battery()
        height = drone.get_height()
        pitch = drone.get_pitch()
        roll = drone.get_roll()
        yaw = drone.get_yaw()

        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                timestamp, "", state, battery, height, 
                pitch, roll, yaw, detected, detection_val
            ])
    except Exception as e:
        print(f"[LOG ERROR] Failed to record telemetry: {e}")

def log_message(message, channel = "", state = ""):
    """Appends a simple log message with timestamp to the CSV."""

    color = RESET
    if channel == "[INFO]":
        color = GREEN
    elif channel == "[STATE]":
        color = BLUE
    elif channel == "[WARNING]" or channel == "[ALERT]":
        color = YELLOW
    elif channel == "[ERROR]":
        color = RED

    message = message.replace("{state}", state).replace("{channel}", channel) if message else "Empty message"
    print(f"{color}{channel} {state}: {message}{RESET}".strip())

    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, f"{channel} {state}: {message}", state])
    except Exception as e:
        print(f"[LOG ERROR] Failed to record message: {e}")