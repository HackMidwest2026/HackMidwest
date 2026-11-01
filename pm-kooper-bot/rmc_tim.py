"""Frame-counted wrapper: every e.step(.., 2) from the start state is one game frame (30 fps)."""
import math
from emu import *
from pm import *
import pra02_block_clip as BC
START = 'states/pra02_topdoor_closed.st'   # frame the pra_02 top door finishes closing
class T:
    def __init__(s, e): s.e = e; s.n = 0; BC.e = e; s.log = {}
    def start(s): s.e.load(START); s.n = 0
    def step(s, b=0, x=0, y=0): s.e.step(b, x, y, 2); s.n += 1; s.log[s.n] = (b, x, y)
    def go(s, tx, tz, maxf=400, tol=0.5, mn=14):
        for f in range(maxf):
            p = player(s.e); dx, dz = tx - p['x'], tz - p['z']; d = math.hypot(dx, dz)
            if d < tol: return True
            mag = max(mn, min(80, int(d * 10)))
            s.step(0, int(round(mag * dx / d)), int(round(-mag * dz / d)))
        return False
    def wait(s, k):
        for i in range(k): s.step()
    def pstep(s, gap=4):
        p = player(s.e); l = BC.laki(); tx, tz = l['x'] - gap, l['z']
        d = math.hypot(tx - p['x'], tz - p['z'])
        st = BC.st(math.degrees(math.atan2(tz - p['z'], tx - p['x'])), max(18, min(80, int(d * 8)))) if d > 0.8 else (0, 0)
        s.step(0, *st)
def push(t, gap=3, fac=16, mn=10, mx=80, stop=930):
    e = t.e
    for f in range(2000):
        p = player(e); l = BC.laki(); tx, tz = l['x'] - gap, l['z']
        d = math.hypot(tx - p['x'], tz - p['z'])
        s_ = BC.st(math.degrees(math.atan2(tz - p['z'], tx - p['x'])), max(mn, min(mx, int(d * fac)))) if d > 0.8 else (0, 0)
        t.step(0, *s_)
        if BC.laki()['x'] > stop: return
def corner(t, W2=25):
    t.go(130, -80)
    for i in range(W2): t.step(0, -56, 56)
    l = BC.laki(); t.go(l['x'] - 4, l['z'], 80, 0.3)
def go_spin(t, tx, tz, maxf=600, tol=0.5, stop_spin=30, mn=14):
    """steer at full tilt toward (tx,tz), re-pressing Z whenever Mario is walking/running and still far away."""
    e = t.e; lastz = False
    for f in range(maxf):
        p = player(e); dx, dz = tx - p['x'], tz - p['z']; d = math.hypot(dx, dz)
        if d < tol: return True
        mag = max(mn, min(80, int(d * 10)))
        b = 0
        if d > stop_spin and p['action'] in (0, 1, 2) and not lastz: b = Z
        lastz = bool(b)
        t.step(b, int(round(mag * dx / d)), int(round(-mag * dz / d)))
    return False
CHAIN = None   # set to a spin frame (e.g. 21) to jump out of every spin there (A 1 frame) and re-spin on landing
def go_fast(t, tx, tz, rc=40, far=60, tol=0.5, maxf=600, mn=14):
    """spin-dash toward (tx,tz); jump-cancel the spin once within rc; walk the last bit. With CHAIN set, a spin that
    is still far from the target is also cut by a 1-frame jump on spin frame CHAIN, skipping its end lag."""
    e = t.e; lastz = False; k = 0
    for f in range(maxf):
        p = player(e); dx, dz = tx - p['x'], tz - p['z']; d = math.hypot(dx, dz)
        if d < tol and p['action'] in (0, 1, 2): return True
        a = p['action']; b = 0
        k = k + 1 if a == 26 else 0
        if a == 26 and d < rc: b = A
        elif a == 26 and CHAIN and k == CHAIN: b = A
        elif a in (0, 1, 2) and d > far and not lastz: b = Z
        lastz = b == Z
        mag = max(mn, min(80, int(d * 10))) if d > 0.01 else 0
        t.step(b, int(round(mag * dx / max(d, 1e-6))), int(round(-mag * dz / max(d, 1e-6))))
    return False
def door_press(t, stick, cmax=80, extra=0):
    """Hold `stick` (walking into the door) and find the earliest frame on which a single A press opens the door.
    Returns (frame number of that A input counted from the start, frame the room changes). `extra` adds a button
    held with the stick (e.g. nothing)."""
    e = t.e; room = where(e)[:2]
    t.step(0, *stick)
    S = '/dev/shm/pmbot/dp_%d.st' % id(t); e.save(S); n1 = t.n
    for c in range(cmax):
        e.load(S); t.n = n1
        for i in range(c): t.step(extra, *stick)
        t.step(A | extra, *stick); af = t.n
        for i in range(90):
            t.step(0, *stick)
            if where(e)[:2] != room: return af, t.n
    return None, None
def to_door(t, tx, tz, stick, rc=40, far=60, stopd=25, cmax=60):
    """spin toward (tx,tz) until within stopd, then hold `stick` into the door and find the earliest single A."""
    go_fast(t, tx, tz, rc, far, stopd)
    return door_press(t, stick, cmax)
def ride(t, tx, tz, k):
    for f in range(k):
        p = player(t.e); dx, dz = tx - p['x'], tz - p['z']; d = max(1e-6, math.hypot(dx, dz))
        t.step(0, int(80 * dx / d), int(-80 * dz / d))
def dismount(t, stick=(0, 0)):
    t.step(B, *stick)
    for i in range(40):
        if player(t.e)['action'] in (0, 1, 2): return
        t.step(0, *stick)
