# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
import main as flight_main


class TelloLauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tello EDU Flight Control Panel")
        self.root.geometry("450x700")
        self.root.resizable(False, False)

        # Style Configuration
        style = ttk.Style()
        style.theme_use('clam')

        # Header Label
        ttk.Label(root, text="Tello Flight Configuration", font=("Helvetica", 14, "bold")).pack(pady=10)

        # --- SECTION 1: Detection Strategy ---
        frame_mode = ttk.LabelFrame(root, text=" Detection Mode ")
        frame_mode.pack(fill="x", padx=15, pady=5)

        self.mode_var = tk.StringVar(value="OPTION_A")
        ttk.Radiobutton(frame_mode, text="Option A: Mission Pad (SDK 2.0)", variable=self.mode_var, value="OPTION_A", command=self.toggle_mode_fields).pack(anchor="w", padx=10, pady=2)
        ttk.Radiobutton(frame_mode, text="Option B: OpenCV Color Mask", variable=self.mode_var, value="OPTION_B", command=self.toggle_mode_fields).pack(anchor="w", padx=10, pady=2)

        # --- SECTION 2: Option A Parameters ---
        self.frame_opt_a = ttk.LabelFrame(root, text=" Mission Pad Settings ")
        self.frame_opt_a.pack(fill="x", padx=15, pady=5)

        ttk.Label(self.frame_opt_a, text="Target Pad ID (1-8):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.pad_id_entry = ttk.Spinbox(self.frame_opt_a, from_=1, to=8, width=5)
        self.pad_id_entry.set(1)
        self.pad_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # --- SECTION 3: Option B Parameters ---
        self.frame_opt_b = ttk.LabelFrame(root, text=" OpenCV HSV Settings ")
        self.frame_opt_b.pack(fill="x", padx=15, pady=5)

        ttk.Label(self.frame_opt_b, text="Preset Target Color:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.color_preset = ttk.Combobox(self.frame_opt_b, values=["Red Object", "Blue Object", "Green Object"], state="readonly", width=15)
        self.color_preset.set("Red Object")
        self.color_preset.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(self.frame_opt_b, text="Min Coverage Threshold (%):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.threshold_slider = ttk.Scale(self.frame_opt_b, from_=5, to=50, value=15)
        self.threshold_slider.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # --- SECTION 4: Movement Settings ---
        frame_movement = ttk.LabelFrame(root, text=" Movement Settings ")
        frame_movement.pack(fill="x", padx=15, pady=5)

        ttk.Label(frame_movement, text="Movement Mode:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.movement_mode = ttk.Combobox(
            frame_movement,
            values=["STEPWISE", "CONTINUOUS"],
            state="readonly",
            width=15,
        )
        self.movement_mode.set("STEPWISE")
        self.movement_mode.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame_movement, text="Step Distance (cm):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.step_distance = ttk.Spinbox(frame_movement, from_=1, to=100, width=5)
        self.step_distance.set(20)
        self.step_distance.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame_movement, text="Maximum Distance (cm):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.max_distance = ttk.Spinbox(frame_movement, from_=1, to=2000, width=5)
        self.max_distance.set(300)
        self.max_distance.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame_movement, text="Forward Speed (cm/s):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.speed_slider = ttk.Scale(frame_movement, from_=10, to=100, value=30)
        self.speed_slider.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # --- SECTION 5: Control Buttons ---
        self.btn_apply = tk.Button(root, text="APPLY SETTINGS", command=self.apply_settings)
        self.btn_apply.pack(fill="x", padx=15, pady=(10, 5))

        self.btn_launch = tk.Button(root, text="START MISSION", bg="#2ecc71", fg="white", font=("Helvetica", 12, "bold"), command=self.launch_flight)
        self.btn_launch.pack(fill="x", padx=15, pady=15)

        # Status Footer
        self.status_label = ttk.Label(root, text="Status: Ready for takeoff", font=("Helvetica", 9, "italic"))
        self.status_label.pack(side="bottom", pady=5)

        self.toggle_mode_fields()

    def toggle_mode_fields(self):
        """Enables/Disables sub-settings panels depending on mode."""
        if self.mode_var.get() == "OPTION_A":
            for child in self.frame_opt_a.winfo_children():
                child.configure(state="normal")
            for child in self.frame_opt_b.winfo_children():
                child.configure(state="disabled")
        else:
            for child in self.frame_opt_a.winfo_children():
                child.configure(state="disabled")
            for child in self.frame_opt_b.winfo_children():
                child.configure(state="normal")

    def get_hsv_ranges(self):
        preset = self.color_preset.get()
        if preset == "Red Object":
            return [0, 120, 70], [10, 255, 255]
        elif preset == "Blue Object":
            return [100, 150, 0], [140, 255, 255]
        elif preset == "Green Object":
            return [36, 25, 25], [86, 255, 255]
        return [0, 120, 70], [10, 255, 255]

    def apply_settings(self, show_error=True):
        try:
            lower_hsv, upper_hsv = self.get_hsv_ranges()
            flight_main.DETECTION_MODE = self.mode_var.get()
            flight_main.MOVEMENT_MODE = self.movement_mode.get()
            flight_main.STEP_DISTANCE_CM = int(self.step_distance.get())
            flight_main.MAX_DISTANCE_CM = int(self.max_distance.get())
            flight_main.TARGET_PAD_ID = int(self.pad_id_entry.get())
            flight_main.FORWARD_SPEED = int(self.speed_slider.get())
            flight_main.LOWER_HSV = lower_hsv
            flight_main.UPPER_HSV = upper_hsv
            flight_main.COLOR_COVERAGE_THRESHOLD = self.threshold_slider.get() / 100.0
        except ValueError:
            if show_error:
                messagebox.showerror("Invalid settings", "Enter valid numeric flight settings before starting.")
            return False

        self.status_label.config(text="Status: Settings applied to main.py")
        return True

    def launch_flight(self):
        if not self.apply_settings():
            return

        self.btn_launch.config(state="disabled", text="MISSION IN PROGRESS...", bg="#7f8c8d")
        self.btn_apply.config(state="disabled")
        self.status_label.config(text="Status: Drone active...")

        # Spawn background thread so GUI doesn't freeze during execution
        flight_thread = threading.Thread(target=self._run_thread, daemon=True)
        flight_thread.start()

    def _run_thread(self):
        try:
            flight_main.main()
        except Exception as error:
            self.root.after(0, lambda: messagebox.showerror("Flight error", str(error)))
        self.root.after(0, self._on_flight_complete)

    def _on_flight_complete(self):
        self.btn_launch.config(state="normal", text="START MISSION", bg="#2ecc71")
        self.btn_apply.config(state="normal")
        self.status_label.config(text="Status: Mission completed / Landed")
        messagebox.showinfo("Flight Status", "Mission complete. Telemetry recorded in logs/flight_log.csv")


if __name__ == "__main__":
    root = tk.Tk()
    app = TelloLauncherGUI(root)
    root.mainloop()