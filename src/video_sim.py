import math
import time

import cv2
import pygame
import physicsSim   # top-level module that djitellopySim itself imports

_PATCHED = False


def _patch_pygame_once():
    """Wrap the sim's drone drawing so it also draws the target ball."""
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    original = physicsSim.sim._draw_drone_3d

    def draw_drone_then_target(sim, tello):
        original(sim, tello)
        target = getattr(tello, "sim_target", None)
        if target is None:
            return
        tx, ty = target.target_position()
        ground = sim._world_to_screen(tx, ty, 0)
        centre = sim._world_to_screen(tx, ty, target.height)
        r = max(6, int(target.radius_cm * 0.6 * sim.camera_zoom))
        pygame.draw.ellipse(sim.screen, (4, 7, 10),
                            pygame.Rect(ground[0] - r * 1.2, ground[1] - r * 0.4, r * 2.4, r * 0.8), 1000)
        pygame.draw.circle(sim.screen, (30, 30, 30), (int(centre[0]), int(centre[1])), r)
        pygame.draw.circle(sim.screen, (248, 250, 252), (int(centre[0]), int(centre[1])), r, 3)

    physicsSim.sim._draw_drone_3d = draw_drone_then_target


class ProjectedTargetReader:
    """Fake camera plus pygame marker for a moving dark ball, both driven by the
    sim drone's true position and heading."""

    def __init__(self, original_reader, drone, start_distance=300, speed=50,
                 sway=300, move_s=20, radius_cm=50, focal_px=230):
        self.original_reader = original_reader
        self.drone = drone
        self.radius_cm = radius_cm
        self.focal_px = focal_px      # 230 is about an 80 degree FOV at 400 px wide
        self.speed = speed            # drift speed, cm/s
        self.sway = sway              # sideways sway amplitude, cm
        self.move_s = move_s          # target stops after this many seconds
        self.height = 1.8             # sim height units, matches takeoff height
        self.t0 = None

        # Target path is defined relative to the drone's starting pose
        x, y = drone.drone["pos"][0], drone.drone["pos"][1]
        h = math.radians(drone.drone["rot"])
        self.fwd = (math.sin(h), math.cos(h))
        self.right = (math.cos(h), -math.sin(h))
        self.start = (x + start_distance * self.fwd[0],
                      y + start_distance * self.fwd[1])

        drone.sim_target = self       # lets the pygame patch find the target
        _patch_pygame_once()

    def target_position(self):
        t = 0 if self.t0 is None else min(time.time() - self.t0, self.move_s)
        ahead = self.speed * t
        side = self.sway * math.sin(0.5 * t)
        return (self.start[0] + ahead * self.fwd[0] + side * self.right[0],
                self.start[1] + ahead * self.fwd[1] + side * self.right[1])

    @property
    def frame(self):
        if self.t0 is None:
            self.t0 = time.time()     # target starts moving on the first frame read
        self.drone._render_frame(apply_wind=False)   # keep pygame redrawing every loop

        base = self.original_reader.frame
        if base is None:
            return None
        frame = base.copy()
        h_img, w_img = frame.shape[:2]

        tx, ty = self.target_position()
        px, py = self.drone.drone["pos"][0], self.drone.drone["pos"][1]
        h = math.radians(self.drone.drone["rot"])
        dx, dy = tx - px, ty - py
        ahead = dx * math.sin(h) + dy * math.cos(h)
        side = dx * math.cos(h) - dy * math.sin(h)

        if ahead > 20:
            u = int(w_img / 2 + self.focal_px * side / ahead)
            r = int(self.focal_px * self.radius_cm / ahead)
            if -r < u < w_img + r:
                cv2.circle(frame, (u, h_img // 2), r, (20, 20, 20), -1)
        return frame