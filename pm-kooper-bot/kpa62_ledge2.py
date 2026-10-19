"""kpa_62 setup from the y-35 ledge, version 2: ledge fixed point (hold RIGHT), optional spin, jump (A held a frames,
RIGHT held d frames) up onto the y-60 platform, then LEFT for k frames (k 1..40, x gets pinned on the raised platform's
east face), then DOWN for b frames, b predicted from 3.215 units/axis/frame and tried +-1. On-line spots get the clip
check; prints every clipping program.
usage: kpa62_ledge2.py STATE PART NPARTS OUT.jsonl"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
A, Z = 0x0080, 0x0020
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kl2%d' % os.getpid())
tmp = '/dev/shm/pmbot/kl2%d' % os.getpid()
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
jobs = [(pre, a, d) for pre in pres for a in (25, 8) for d in range(0, 26)][PART::NP]
fo = open(out, 'a'); hits = 0
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
    for k in range(1, 41):
        e.load(tmp + '.l')
        for i in range(k): e.step(0, *CARD['left'], 2)
        for i in range(20): e.step(0, 0, 0, 2)
        q = player(e)
        if abs(q['y'] - 60) > .5: break
        e.save(tmp + '.k')
        b0 = round((-440.69 - q['x']) / 3.215)
        for b in (b0 - 1, b0, b0 + 1):
            if b < 1: continue
            e.load(tmp + '.k')
            for i in range(b): e.step(0, *CARD['down'], 2)
            for i in range(20): e.step(0, 0, 0, 2)
            s = player(e)
            if not on_line(s): continue
            ok = clip(); hits += ok
            rec = {'pre': pre, 'jumpA': a, 'd': d, 'land': [p['x'], p['z']], 'left': k, 'down': b, 'stand': [s['x'], s['z']], 'clip': ok}
            fo.write(json.dumps(rec) + '\n'); fo.flush()
            if ok: print(rec, flush=True)
print('done part', PART, len(jobs), 'jobs', hits, 'clips')
