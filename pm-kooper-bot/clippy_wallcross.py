"""Clippy wall-crossing test, nok_13 plateau, no teleports. From the post-flee clippy state (counter -1), Mario walks
to a grid point (skipped if he cannot reach it), then holds one world direction for 90 game frames, plain or spinning
every 30 frames. A hit is a frame-to-frame move that crosses a solid wall from data/nok13_collision.json. Each run is
repeated with the counter written back to 0 as the control. usage: clippy_wallcross.py STATE PART NPARTS OUT.jsonl"""
import json, math, sys
from emu import *
from pm import *
from nav import stick_world
st0, part, nparts, outp = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
def seg_cross(p, q, a, b):
    def o(u, v, w): return (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    return o(p, q, a) * o(p, q, b) < 0 and o(a, b, p) * o(a, b, q) < 0
walls = []
for c in json.load(open('nok13_collision.json'))['colliders']:
    if c['flags'] & 0x10000: continue
    for t in c['tris']:
        if abs(t['n'][1]) > 0.5: continue
        pts = [(v[0], v[2]) for v in t['v']]
        a, b = max(((p, q) for p in pts for q in pts), key=lambda pq: math.dist(*pq))
        if math.dist(a, b) < 0.5: continue
        ys = [v[1] for v in t['v']]
        walls.append((c['id'], a, b, min(ys), max(ys)))
def crossed(p, q, y):
    for cid, a, b, y0, y1 in walls:
        if y0 < y + 10 and y1 > y + 25 and seg_cross(p, q, a, b): return cid
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cwx%d' % part)
pts = [(x, z) for x in range(-940, -480, 30) for z in range(-130, 80, 30)]
jobs = [(pt, yaw, spin) for pt in pts for yaw in range(0, 360, 15) for spin in (0, 1)][part::nparts]
out = open(outp, 'a'); reach = {}
for (px, pz), yaw, spin in jobs:
    for cnt in (-1, 0):
        e.load(st0)
        if cnt == 0: e.w8(PLAYER + 0x14, 0)
        ok = False
        for f in range(250):
            p = player(e)
            if math.hypot(px - p['x'], pz - p['z']) < 4: ok = True; break
            s = stick_world(e, math.degrees(math.atan2(px - p['x'], -(pz - p['z']))) % 360); e.step(0, s[0], s[1], 2)
            if e.s16(GAME_MODE) != 4: break
        if not ok: break
        p0 = player(e); hit = None
        for f in range(90):
            s = stick_world(e, yaw); e.step(Z if spin and f % 30 == 0 else 0, s[0], s[1], 2)
            if e.s16(GAME_MODE) != 4: break
            p1 = player(e)
            w = crossed((p0['x'], p0['z']), (p1['x'], p1['z']), min(p0['y'], p1['y']))
            if w is not None: hit = (f, w, round(p1['x'], 1), round(p1['y'], 1), round(p1['z'], 1)); break
            p0 = p1
        r = {'pt': (px, pz), 'yaw': yaw, 'spin': spin, 'cnt': cnt, 'hit': hit}
        out.write(json.dumps(r) + '\n'); out.flush()
        if hit: print('HIT', r, flush=True)
print('done', part)
