import time
import cv2
import numpy as np
# from djitellopy import Tello
from djitellopySim import Tello
import video_sim as vs

# Dark object range (OpenCV hue is 0-179, low Value = dark)
LOWER_DARK = np.array([0, 0, 0])
UPPER_DARK = np.array([179, 255, 60])

MIN_AREA = 0.01          # ignore blobs smaller than 1% of the frame
TARGET_AREA = 0.15       # blob size to hold (bigger = drone stays closer)

DEADBAND_X = 0.10        # horizontal error ignored inside this
DEADBAND_AREA = 0.03     # size error ignored inside this

MAX_SPEED = 60           # the only speed knob (rc units, max 100)
FULL_SPEED_X = 0.5       # horizontal error at which yaw reaches MAX_SPEED
FULL_SPEED_AREA = 0.10   # size error at which forward reaches MAX_SPEED

IDLE_TIMEOUT_S = 5       # land after this many seconds without movement

def find_dark_object(frame):
    """Returns (cx, area_ratio, bbox) of the largest dark blob, or None."""
    if frame is None:
        return None

    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (7, 7), 0), cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_DARK, UPPER_DARK)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    area_ratio = cv2.contourArea(largest) / float(h * w)
    if area_ratio < MIN_AREA:
        return None

    x, y, bw, bh = cv2.boundingRect(largest)
    return (x + bw / 2) / w, area_ratio, (x, y, bw, bh)

def scaled_speed(err, deadband, full_speed_err):
    """0 inside the deadband, then ramps linearly up to MAX_SPEED."""
    if abs(err) <= deadband:
        return 0
    return int(MAX_SPEED * max(-1, min(1, err / full_speed_err)))


def follow_command(cx, area):
    """Returns (forward, yaw). Zero means no correction needed."""
    x_err = (cx - 0.5) * 2            # +1 = object at right edge
    a_err = TARGET_AREA - area        # positive = object too far

    forward = scaled_speed(a_err, DEADBAND_AREA, FULL_SPEED_AREA)
    yaw = scaled_speed(x_err, DEADBAND_X, FULL_SPEED_X)
    return forward, yaw

def main():
    drone = Tello()
    drone.is_windy = False
    drone.connect()
    print(f"Battery: {drone.get_battery()}%")

    drone.streamon()
    reader = drone.get_frame_read()
    reader = vs.ProjectedTargetReader(reader, drone)
    time.sleep(2)  # warm up video feed

    drone.takeoff()
    last_motion = time.time()

    try:
        while True:
            frame = reader.frame
            target = find_dark_object(frame)

            if target is None:
                forward, yaw = 0, 0          # nothing to follow, hover
            else:
                forward, yaw = follow_command(target[0], target[1])

            drone.send_rc_control(0, forward, 0, yaw)

            # Any correction means the object moved (or we are still closing in)
            now = time.time()
            if forward or yaw:
                last_motion = now
            idle = now - last_motion

            if frame is not None:
                view = frame.copy()
                if target is not None:
                    x, y, bw, bh = target[2]
                    cv2.rectangle(view, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
                cv2.putText(view, f"Idle: {idle:.1f}/{IDLE_TIMEOUT_S}s", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Tello Camera Feed", view)
                cv2.waitKey(1)

            if idle >= IDLE_TIMEOUT_S:
                print("No movement for 5s. Landing.")
                break

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Interrupted. Landing.")

    finally:
        drone.send_rc_control(0, 0, 0, 0)
        drone.land()
        drone.streamoff()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()