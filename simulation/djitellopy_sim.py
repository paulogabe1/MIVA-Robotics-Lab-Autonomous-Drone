import time
from djitellopySim import Tello  # Replace with djitellopy when on real hardware


def run_flight():
    # 1. Initialize and connect
    drone = Tello()
    drone.connect()

    print(f"[STATUS] Initial Battery Level: {drone.get_battery()}%")
    print(f"[STATUS] Initial Height: {drone.get_height()} cm")

    # 2. Takeoff
    print("\n[ACTION] Taking off...")
    drone.takeoff()
    time.sleep(1)

    # 3. Flight Maneuvers
    print("[ACTION] Flying forward 150 cm...")
    drone.move_forward(150)
    time.sleep(1)

    print("[ACTION] Rotating 180 degrees...")
    drone.rotate_clockwise(180)
    time.sleep(1)

    print("[ACTION] Returning to start (150 cm forward)...")
    drone.move_forward(150)
    time.sleep(1)

    # 4. Landing
    print("\n[ACTION] Landing...")
    drone.land()

    # 5. Display DONE status and freeze window open
    print("\n==============================")
    print("      FLIGHT STATUS: DONE     ")
    print("==============================")

    # Keeps the Python process and simulator window open until you hit Enter
    input("\n[SIMULATOR] Press [ENTER] in this terminal to exit and close the window...")


if __name__ == "__main__":
    run_flight()