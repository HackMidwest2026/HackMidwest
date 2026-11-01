import math
from rmc_tim import *
def v2_finish(t, first=3, ang=55, pause=4, maxf=120):
    """v2 RTA ending after the push stops: fixed stick angle, full jump on frame `first`, `pause` floor frames, A5 hop, C-down on block."""
    e = t.e
    stick = (int(round(-80 * math.cos(math.radians(ang)))), int(round(-80 * math.sin(math.radians(ang)))))
    jt = None; hops = 0; land = None; cd = None
    for f in range(maxf):
        p = player(e); grounded = p['action'] in (0, 1, 2)
        if grounded and p['y'] > 14:
            t.step(D_CBUTTON, *stick); cd = t.n; break
        if grounded and hops == 1 and land is None and jt is None: land = f
        b = 0
        start = (hops == 0 and f >= first) or (hops == 1 and land is not None and f >= land + pause)
        if jt is None and grounded and start: jt = 0; hops += 1
        if jt is not None:
            b = A if jt < (5 if hops == 2 else 8) else 0; jt += 1
            if jt > 4 and grounded: jt = None
        t.step(b, *stick)
    return cd
def clipped(t, k=40):
    for i in range(k): t.step()
    p = player(t.e); return p['z'] > 1 and p['y'] > 0
def v1_finish(t, k=10, ha=5, tgt=(865, -90), maxf=80):
    """v1: run k frames toward the block, then chain A-held-`ha` hops aimed at tgt; C-down on the first block frame."""
    e = t.e; jt = None
    for f in range(maxf):
        p = player(e); grounded = p['action'] in (0, 1, 2)
        if grounded and p['y'] > 14:
            t.step(D_CBUTTON); return t.n
        dx, dz = tgt[0] - p['x'], tgt[1] - p['z']; d = math.hypot(dx, dz)
        stick = (0, 0) if d < 3 else (int(80 * dx / d), int(-80 * dz / d))
        b = 0
        if f >= k:
            if jt is None and grounded: jt = 0
            if jt is not None:
                b = A if jt < ha else 0; jt += 1
                if jt > 4 and grounded: jt = None
        t.step(b, *stick)
    return None
AIR = (3, 4, 5, 6, 8, 15)
def v3_climb(t, wait8=8, log=None):
    """neutral v3 from the cave-mouth spot (Mario already at ~(535,-60) standing): left to x 510, wait, TJ1 (left 40),
    2 frames, neutral J+TJ2, 2 frames, J3 down-left 8 then down. Returns frame of first south-of-mirror landing or None."""
    e = t.e
    for f in range(60):
        if player(e)['x'] <= 510: break
        t.step(0, -80, 0)
    for i in range(wait8 + 1): t.step()
    for f in range(45):
        t.step(A if (f < 5 or 10 <= f < 12) else 0, -40, 0)
        if f > 3 and player(e)['action'] not in AIR: break
    t.step(); t.step()
    for f in range(60):
        t.step(A if (f < 5 or 6 <= f < 8) else 0, 0, 0)
        if f > 3 and player(e)['action'] not in AIR: break
    if log: log('TJ2 landed at %s %s' % (t.n, player(e)))
    t.step(); t.step()
    for f in range(140):
        t.step(A if f < 8 else 0, *((-56, -56) if f < 8 else (0, -80)))
        p = player(e)
        if where(e)[:2] != (21, 0): return None
        if f > 10 and p['action'] in (0, 1, 2) and p['z'] > 0.5: return t.n
    return None
