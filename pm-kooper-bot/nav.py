"""Camera-aware walking: steer Mario toward world points by converting the world direction to a stick angle with
the current camera yaw (gCameras[0].curYaw). Stick angle 0 = up; Mario's world yaw = stick angle + camera yaw,
world yaw 0 = -z, 90 = +x."""
import math
from pm import *
CAM_YAW = 0x800B1D60 + 0x6C
def stick_world(e, wyaw, mag=80):
    a = math.radians(wyaw - e.f32(CAM_YAW))
    return int(round(mag * math.sin(a))), int(round(mag * math.cos(a)))
def world_yaw_to(p, x, z):
    return math.degrees(math.atan2(x - p['x'], -(z - p['z']))) % 360
def go_to(e, x, z, maxf=400, tol=8.0, buttons=0, log=None):
    """walk until within tol of (x, z); returns frames used (game frames) and whether it arrived"""
    last, stuck = None, 0
    for f in range(maxf):
        p = player(e)
        if math.hypot(p['x'] - x, p['z'] - z) < tol: return f, True
        sx, sy = stick_world(e, world_yaw_to(p, x, z))
        e.step(buttons, sx, sy, 2)
        if log is not None: log.append((sx, sy))
        q = player(e)
        if last and math.hypot(q['x'] - last[0], q['z'] - last[1]) < 0.05: stuck += 1
        else: stuck = 0
        if stuck > 15: return f, False
        last = (q['x'], q['z'])
    return maxf, False
