"""kpa_62 setup from the y-35 ledge below (collider 22), where a run arrives from. Fixed point: hold RIGHT on the ledge
(converges to (-518.77, 35, -18.23)). From there: optional spin (Z + cardinal S held s frames), then a jump (A held a
frames) with cardinal D held d frames from the jump, landing on the y-60 platform; then optionally one cardinal walk W
for k frames (predicted from 3.215 units/axis/frame, simulated only when it would land within 0.6 of the line).
Spots on the line (x -440.80..-440.58, z -60..-40) get the full clip check (settle, mount, ride, B, down, C-down 34).
usage: kpa62_ledge.py STATE PART NPARTS OUT.jsonl"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
VEC = {'right': (1, -1), 'down': (1, 1), 'left': (-1, 1), 'up': (-1, -1)}
A, Z = 0x0080, 0x0020
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kld%d' % os.getpid())
tmp = '/dev/shm/pmbot/kld%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); place(e, -505.0, -20.0, y=35.0)
for i in range(150): e.step(0, *CARD['right'], 2)
for i in range(30): e.step(0, 0, 0, 2)
fp = player(e); e.save(tmp + '.fp')
if PART == 0: print('ledge fixed point (%.3f %.1f %.3f)' % (fp['x'], fp['y'], fp['z']), flush=True)
def on_line(p): return -440.80 <= p['x'] <= -440.58 and -60 <= p['z'] <= -40 and abs(p['y'] - 60) < .5
def clip():
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    dn = CARD['down']
    for fr in range(1, 34): e.step(0, *dn, 2)
    e.step(0x400, *dn, 2)
    for f in range(30):
        e.step(0, *dn, 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']): return True
    return False
pres = [None] + [(s, k) for s in CARD for k in (1, 6, 12)]
jobs = [(pre, a, D) for pre in pres for a in (25, 8) for D in CARD][PART::NP]
fo = open(out, 'a'); hits = 0; landed = 0
for (pre, a, D) in jobs:
    for d in range(0, 26):
        e.load(tmp + '.fp')
        if pre:
            e.step(Z, *CARD[pre[0]], 2)
            for i in range(pre[1] - 1): e.step(0, *CARD[pre[0]], 2)
        for f in range(45):
            b = A if f < a else 0
            e.step(b, *(CARD[D] if f < d else (0, 0)), 2)
        for i in range(10): e.step(0, 0, 0, 2)
        p = player(e)
        if abs(p['y'] - 60) > .5: continue
        landed += 1; e.save(tmp + '.l')
        cands = [(None, 0)] + [(W, k) for W in CARD for k in range(1, 30)
                               if abs(p['x'] + VEC[W][0] * 3.215 * k + 440.69) < 0.6 and -61 <= p['z'] + VEC[W][1] * 3.215 * k <= -39]
        for (W, k) in cands:
            e.load(tmp + '.l')
            if W:
                for i in range(k): e.step(0, *CARD[W], 2)
                for i in range(20): e.step(0, 0, 0, 2)
            q = player(e)
            if not on_line(q): continue
            ok = clip(); hits += ok
            rec = {'pre': pre, 'jumpA': a, 'D': D, 'd': d, 'land': [p['x'], p['z']], 'walk': [W, k], 'stand': [q['x'], q['z']], 'clip': ok}
            fo.write(json.dumps(rec) + '\n'); fo.flush()
            if ok: print(rec, flush=True)
print('done part', PART, len(jobs), 'jobs', landed, 'landings on y60', hits, 'clips')
