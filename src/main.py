import time
import os
import cv2
# from djitellopy import Tello
from djitellopySim import Tello

# Import detection methods from src/obstacle.py
from obstacle import (
    init_pad_detection,
    check_pad,
    check_color,
    cleanup_pad_detection
)

import logger

# ==========================================
# CONFIG
# ==========================================
# Detection Mode: 'OPTION_A' (Mission Pad) or 'OPTION_B' (HSV Color)
DETECTION_MODE = 'OPTION_B'
MOVEMENT_MODE = 'STEPWISE'  # 'STEPWISE' or 'CONTINUOUS'

# Mission Parameters
STEP_DISTANCE_CM = 20      # Incremental forward step size (cm)
MAX_DISTANCE_CM = 40      # Total distance cap (cm)
TARGET_PAD_ID = 1          # Target Mission Pad ID for Option A

FORWARD_SPEED = 30    # Forward speed in cm/s if using continuous movement (not step-wise)

# Option B HSV Ranges (Default: Red Object)
LOWER_HSV = [0, 120, 70]
UPPER_HSV = [10, 255, 255]
COLOR_COVERAGE_THRESHOLD = 0.15  # 15% frame coverage triggers obstacle

# Logging Setup
LOG_FILE = os.path.join("logs", "flight_log.csv")


def obstacle_detection_check(drone, frame=None):
    """
    Runs the appropriate obstacle detection method based on the selected mode.
    Returns a tuple of (is_detected, detection_value).
    """
    if DETECTION_MODE == 'OPTION_A':
        is_detected, pad_id = check_pad(drone, TARGET_PAD_ID)
        detection_value = f"Pad_ID_{pad_id}" if pad_id != -1 else "No_Pad"

    elif DETECTION_MODE == 'OPTION_B':
        is_detected, fill_ratio = check_color(frame, LOWER_HSV, UPPER_HSV, COLOR_COVERAGE_THRESHOLD)
        detection_value = f"Fill_{fill_ratio:.2%}"

        # --- LIVE CAMERA FEED DISPLAY ---
        if frame is not None:
            # Add status text overlay onto the live frame
            overlay_color = (0, 0, 255) if is_detected else (0, 255, 0)
            status_text = f"OBSTACLE DETECTED ({detection_value})" if is_detected else f"CLEAR ({detection_value})"
            cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, overlay_color, 2)

            # Display frame and process GUI window queue
            cv2.imshow("Tello Camera Feed", frame)
            cv2.waitKey(1)

    else:
        raise ValueError(f"Invalid DETECTION_MODE: {DETECTION_MODE}")

    return is_detected, detection_value


# ==========================================
# MAIN FLIGHT
# ==========================================
def main():
    logger.init_logger()
    
    drone = Tello()
    state = "INIT"
    total_traveled_cm = 0
    camera_reader = None

    try:
        # ----------------------------------
        # STATE: INIT
        # ----------------------------------
        logger.log_message("Connecting to Tello EDU...", "[STATE]", state)
        drone.connect()
        
        battery = drone.get_battery()
        logger.log_message(f"Battery Level: {battery}%", "[STATE]", state)
        if battery < 20:
            raise RuntimeError("Battery too low for safe flight (< 20%). Aborting.")

        if DETECTION_MODE == 'OPTION_A':
            init_pad_detection(drone)
        elif DETECTION_MODE == 'OPTION_B':
            drone.streamon()
            camera_reader = drone.get_frame_read()
            time.sleep(2)  # Warm up video feed

        logger.log_telemetry(drone, state, False, "N/A")

        # ----------------------------------
        # STATE: TAKEOFF
        # ----------------------------------
        state = "TAKEOFF"
        print(f"[STATE] {state}: Initiating takeoff...")
        drone.takeoff()
        time.sleep(1)
        logger.log_telemetry(drone, state, False, "N/A")

        if MOVEMENT_MODE == 'STEPWISE':
            logger.log_message("Step-wise forward movement enabled. Step size: {STEP_DISTANCE_CM} cm", "[INFO]")
            # ----------------------------------
            # STATE: SEARCHING_FORWARD
            # ----------------------------------
            state = "SEARCHING_FORWARD"
            logger.log_message("Starting step-wise forward scan", "[STATE]", state)

            while True:
                obstacle_detected = False
                detection_value = "Clear"

                obstacle_detected, detection_value = obstacle_detection_check(drone, camera_reader.frame if camera_reader else None)

                logger.log_telemetry(drone, state, obstacle_detected, detection_value)

                if total_traveled_cm < MAX_DISTANCE_CM:
                    # 2. State transition
                    if obstacle_detected:
                        state = "OBSTACLE_DETECTED"
                        logger.log_message(f"Obstacle Detected! Value: {detection_value}. Stopping drone.", "[ALERT]", state)
                        break

                    # 3. Step forward incrementally if path is clear
                    logger.log_message(f"Path clear. Stepping forward {STEP_DISTANCE_CM} cm (Total: {total_traveled_cm + STEP_DISTANCE_CM}/{MAX_DISTANCE_CM} cm)", "[INFO]", state)
                    drone.move_forward(STEP_DISTANCE_CM)
                    total_traveled_cm += STEP_DISTANCE_CM
                    time.sleep(0.5)  # Short stabilization pause

        elif MOVEMENT_MODE == 'CONTINUOUS':
            logger.log_message(f"Continuous forward movement enabled. Speed: {FORWARD_SPEED} cm/s", "[INFO]")
            # ----------------------------------
            # STATE: SEARCHING_CONTINUOUS
            # ----------------------------------
            state = "SEARCHING_CONTINUOUS"
            logger.log_message("Moving forward continuously until obstacle detected...", "[STATE]", state)

            # Start moving forward smoothly
            drone.send_rc_control(0, FORWARD_SPEED, 0, 0)

            while True:
                obstacle_detected = False
                detection_value = "Clear"

                obstacle_detected, detection_value = obstacle_detection_check(drone, camera_reader.frame if camera_reader else None)

                logger.log_telemetry(drone, state, obstacle_detected, detection_value)

                # 2. Stop instantly if obstacle detected
                if obstacle_detected:
                    # Halt all motion (hover)
                    drone.send_rc_control(0, 0, 0, 0)
                    time.sleep(0.5)  # Let drone stabilize
                    state = "OBSTACLE_DETECTED"
                    logger.log_message(f"Obstacle Detected! Value: {detection_value}. Stopping drone.", "[ALERT]", state)
                    break

                # Loop delay (checks ~20 times per second)
                time.sleep(0.05)

        if state != "OBSTACLE_DETECTED":
            state = "MISSION_COMPLETE"
            logger.log_message(f"Reached maximum distance without obstacle encounter.", "[STATE]", state)

    except KeyboardInterrupt:
        logger.log_message("Manual interrupt received! Landing immediately...", "[EMERGENCY]")
        state = "EMERGENCY_INTERRUPT"

    except Exception as e:
        state = "ERROR_LAND"
        logger.log_message(f"Unexpected error occurred: {e}", "[ERROR]", state)

    finally:
        # land and cleanup regardless of how the flight ended
        print(f"\n[STATE] LANDING: Descending safely...")
        logger.log_telemetry(drone, state, False, "Finalizing")
        
        try:
            drone.land()
        except Exception as e:
            logger.log_message(f"Landing command failed: {e}", "[ERROR]")

        if DETECTION_MODE == 'OPTION_A':
            cleanup_pad_detection(drone)
        elif DETECTION_MODE == 'OPTION_B':
            try:
                drone.streamoff()
            except Exception:
                pass

        print(f"[FINISHED] Flight log saved to {LOG_FILE}")
        logger.log_message("[FINISHED] Flight session concluded.", "[INFO]", state)


if __name__ == "__main__":
    main()