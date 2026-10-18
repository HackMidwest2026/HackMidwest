"""Scan a room for spots where Lakilester gets pinned in follow state 0 with Mario standing 45 behind him: for every floor sample
point P (GRID spacing) and 8 directions, put Laki at P (20 above the floor), fill the whole history ring with a target
40 units away in that direction, mark the ring full (idx = ptr - 1), put Mario 45 behind Laki and run 50 frames. Pinned = state 0 every frame,
pointer never advances, Laki moves < 3 units over frames 20-50 and is still > 5 from the target.
usage: laki_pin_scan.py STATE COLLISION.json OUT.jsonl [PART NPARTS GRID]"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
st0, coll, out = sys.argv[1:4]
PART, NP = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 1)
GRID = float(sys.argv[6]) if len(sys.argv) > 6 else 10
C = json.load(open(coll)); C = C['colliders'] if isinstance(C, dict) else C
floors = [t for c in C for t in c['tris'] if t['n'][1] > 0.5]
def inside(t, x, z):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = t['v']
    d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
    if abs(d) < 1e-9: return None
    u = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / d; v = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / d
    if u < -1e-6 or v < -1e-6 or u + v > 1 + 1e-6: return None
    return u * ay + v * by + (1 - u - v) * cy
pts = set()
for t in floors:
    xs = [v[0] for v in t['v']]; zs = [v[2] for v in t['v']]
    x = math.ceil(min(xs) / GRID) * GRID
    while x <= max(xs):
        z = math.ceil(min(zs) / GRID) * GRID
        while z <= max(zs):
            y = inside(t, x, z)
            if y is not None: pts.add((x, round(y, 1), z))
            z += GRID
        x += GRID
pts = sorted(pts)[PART::NP]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/lps%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2); e.save('/dev/shm/pmbot/lps%d.st' % os.getpid())
p0 = player(e)
fo = open(out, 'a'); hits = 0
for (x, y, z) in pts:
    for k in range(8):
        a = math.radians(45 * k); tx, tz = x + 40 * math.sin(a), z - 40 * math.cos(a)
        e.load('/dev/shm/pmbot/lps%d.st' % os.getpid())
        l = [n for n in npcs(e) if n['id'] == -4][0]
        e.wf32(l['addr'] + 0x38, x); e.wf32(l['addr'] + 0x3C, y + 20); e.wf32(l['addr'] + 0x40, z)
        for j in range(40):
            e.wf32(HIST + 16 * j + 4, tx); e.wf32(HIST + 16 * j + 8, y); e.wf32(HIST + 16 * j + 12, tz)
        e.w32(PTR, 10); e.w32(IDX, 9); e.w32(STATE, 0)
        # Mario 45 behind Laki (opposite the target): close enough that Laki's speed stays at the 3 / 0.25*d of normal following
        e.wf32(PLAYER + PS_POS, x - 45 * math.sin(a)); e.wf32(PLAYER + PS_POS + 4, y); e.wf32(PLAYER + PS_POS + 8, z + 45 * math.cos(a))
        P, ok, fwd = [], True, 0
        for f in range(50):
            e.step(0, 0, 0, 2)
            l = [n for n in npcs(e) if n['id'] == -4][0]
            if (e.u32(STATE) >> 16) != 0 or e.u32(PTR) != 10: ok = False; break
            fwd |= l['flags'] & 0x4000; P.append((l['x'], l['y'], l['z']))
        if not ok: continue
        mv = max(math.hypot(P[i][0] - P[-1][0], P[i][2] - P[-1][2]) for i in range(20, 50))
        dt = math.hypot(P[-1][0] - tx, P[-1][2] - tz)
        if mv < 3 and dt > 5:
            hits += 1
            fo.write(json.dumps({'start': [x, y, z], 'dir': 45 * k, 'target': [tx, tz], 'laki_end': P[-1], 'moved': mv, 'dist_to_target': dt,
                                 'speed': l['speed'], 'flags': '%08x' % l['flags']}) + '\n'); fo.flush()
print('done part', PART, len(pts), 'points', hits, 'hits')
