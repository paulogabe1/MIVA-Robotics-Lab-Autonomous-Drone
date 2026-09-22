import cv2
import numpy as np

# ==========================================
# OPTION A: Mission Pad Detection Setup
# ==========================================

def init_pad_detection(drone):
    """Enables SDK 2.0 mission pad scanning on the forward camera."""
    drone.enable_mission_pads()
    # 0 = Downward camera, 1 = Forward camera, 2 = Both
    drone.set_mission_pad_detection_direction(1)
    print("[OBSTACLE] Forward Mission Pad detection initialized.")

def check_pad(drone, target_pad_id: int = 1) -> bool:
    """
    Option A: Uses the Tello EDU forward sensor to check for a tagged mission pad.
    Returns True if the target pad ID is detected.
    """
    detected_pad_id = drone.get_detected_pad_id()
    result = detected_pad_id == target_pad_id
    if result:
        print(f"Drone is on the target pad (ID: {target_pad_id}).")
 
    return result

def cleanup_pad_detection(drone):
    """Disables mission pad scanning on mission wrap-up."""
    try:
        drone.disable_mission_pads()
        print("[OBSTACLE] Mission Pad detection disabled.")
    except Exception as e:
        print(f"[OBSTACLE] Error disabling mission pads: {e}")

# ==========================================
# OPTION B: OpenCV Color Mask Detection
# ==========================================

def check_color(frame, lower_hsv: list, upper_hsv: list, area_threshold: float = 0.15) -> bool:
    """
    Option B: Analyzes the camera video frame with OpenCV to detect if a bright
    color card fills more than a set percentage of the view.
    """
    if frame is None or frame.size == 0:
        return False

    # Convert the video frame from BGR to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Create a binary mask for pixels falling inside the HSV color range
    mask = cv2.inRange(hsv, np.array(lower_hsv), np.array(upper_hsv))
    
    # Calculate what fraction of the screen the target color occupies
    color_pixels = cv2.countNonZero(mask)
    total_pixels = frame.shape[0] * frame.shape[1]
    coverage_ratio = color_pixels / float(total_pixels)

    if coverage_ratio >= area_threshold:
        print(f"[OBSTACLE] Color target detected! Covers {coverage_ratio:.1%} of frame.")
        return True
        
    return False
