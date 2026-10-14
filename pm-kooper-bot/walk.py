"""walking helpers for nok_14: steer mario through waypoints and watch for battles."""
import math
from emu import *
from pm import *


def stick_to(e, tx, tz, maxmag=80):
    p = player(e)
    dx, dz = tx - p['x'], tz - p['z']
    d = math.hypot(dx, dz)
    if d < 1:
        return 0, 0, d
    m = maxmag if d > 20 else max(15, min(maxmag, d * 3))
    return int(dx / d * m), int(-dz / d * m), d


def walk_route(e, points, max_frames=600, log=None, tol=3):
    """walk through (x, z) waypoints. returns (ok, frames); ok is False if a battle/other mode starts."""
    ti, f = 0, 0
    while f < max_frames and ti < len(points):
        sx, sy, d = stick_to(e, *points[ti])
        if d < tol:
            ti += 1
            continue
        e.step(0, sx, sy, 2)
        f += 1
        if log is not None:
            log.append(dict(player(e), f=f, mode=e.s16(GAME_MODE)))
        if e.s16(GAME_MODE) != GM_WORLD:
            return False, f
    return ti == len(points), f
