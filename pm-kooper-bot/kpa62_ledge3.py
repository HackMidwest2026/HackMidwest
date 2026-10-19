"""kpa_62 setup from the y-35 ledge, version 3: ledge fixed point (hold RIGHT), optional spin, jump (A held a frames,
RIGHT held d frames) onto the y-60 platform, then two cardinal walks (W1 k1 frames, W2 k2 frames). Walk end points are
predicted from 3.215 units/axis/frame; only programs predicted within 0.35 of the line are simulated and clip-checked.
usage: kpa62_ledge3.py STATE PART NPARTS OUT.jsonl"""
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
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kl3%d' % os.getpid())
tmp = '/dev/shm/pmbot/kl3%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); place(e, -505.0, -20.0, y=35.0)
for i in range(150): e.step(0, *CARD['right'], 2)
for i in range(30): e.step(0, 0, 0, 2)
e.save(tmp + '.fp')
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
jobs = [(pre, a, d) for pre in pres for a in (25, 8) for d in range(0, 30)][PART::NP]
fo = open(out, 'a'); hits = 0; sims = 0
for (pre, a, d) in jobs:
    e.load(tmp + '.fp')
    if pre:
        e.step(Z, *CARD[pre[0]], 2)
        for i in range(pre[1] - 1): e.step(0, *CARD[pre[0]], 2)
    for f in range(45): e.step(A if f < a else 0, *(CARD['right'] if f < d else (0, 0)), 2)
    for i in range(10): e.step(0, 0, 0, 2)
    p = player(e)
    if abs(p['y'] - 60) > .5: continue
    e.save(tmp + '.l')
    for W1 in CARD:
        for W2 in CARD:
            if W2 == W1: continue
            for k1 in range(0 if W1 == 'up' else 1, 26):
                for k2 in range(1, 26):
                    x = p['x'] + 3.215 * (VEC[W1][0] * k1 + VEC[W2][0] * k2)
                    z = p['z'] + 3.215 * (VEC[W1][1] * k1 + VEC[W2][1] * k2)
                    if abs(x + 440.69) > 0.35 or not (-60 <= z <= -40): continue
                    e.load(tmp + '.l'); sims += 1
                    for i in range(k1): e.step(0, *CARD[W1], 2)
                    for i in range(20): e.step(0, 0, 0, 2)
                    for i in range(k2): e.step(0, *CARD[W2], 2)
                    for i in range(20): e.step(0, 0, 0, 2)
                    s = player(e)
                    if not on_line(s): continue
                    ok = clip(); hits += ok
                    rec = {'pre': pre, 'jumpA': a, 'd': d, 'land': [p['x'], p['z']], 'w1': [W1, k1], 'w2': [W2, k2], 'stand': [s['x'], s['z']], 'clip': ok}
                    fo.write(json.dumps(rec) + '\n'); fo.flush()
                    if ok: print(rec, flush=True)
print('done part', PART, len(jobs), 'jobs', sims, 'simulated', hits, 'clips')
