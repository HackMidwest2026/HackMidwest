"""kpa_62 cardinal-only setup grid: from a fixed corner (UP = hold up into the north-west corner; UPR = then hold right),
run two cardinal segments D1 for a frames then D2 for b frames (a, b = 1..AMAX), 20 neutral frames after each; spots on
the line get the full clip check. Writes every on-line spot and its result, to find setups with wide frame windows.
usage: kpa62_card_grid.py STATE PART NPARTS OUT.jsonl   env: CORNERS (UP,UPR), AMAX"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
AMAX = int(os.environ.get('AMAX', '40')); CORNERS = os.environ.get('CORNERS', 'UP,UPR').split(',')
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kcg%d' % os.getpid())
tmp = '/dev/shm/pmbot/kcg%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); place(e, -480.0, -100.0)
for i in range(120): e.step(0, *CARD['up'], 2)
for i in range(10): e.step(0, 0, 0, 2)
e.save(tmp + '.UP')
for i in range(30): e.step(0, *CARD['right'], 2)
for i in range(20): e.step(0, 0, 0, 2)
e.save(tmp + '.UPR')
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
        if f > 18 and q['y'] > 40 and inside_tower(q['x'], q['z']): return True
    return False
jobs = [(c, d1, a) for c in CORNERS for d1 in CARD for a in range(1, AMAX + 1)][PART::NP]
fo = open(out, 'a'); hits = 0
for (c, d1, a) in jobs:
    e.load(tmp + '.' + c)
    for i in range(a): e.step(0, *CARD[d1], 2)
    for i in range(20): e.step(0, 0, 0, 2)
    p1 = player(e)
    if abs(p1['y'] - 60) > .5: continue
    e.save(tmp + '.1')
    for d2 in CARD:
        if d2 == d1: continue
        e.load(tmp + '.1')
        for b in range(1, AMAX + 1):
            e.step(0, *CARD[d2], 2)
            e.save(tmp + '.b')
            for i in range(20): e.step(0, 0, 0, 2)
            p = player(e)
            if abs(p['y'] - 60) > .5: break
            if on_line(p):
                ok = clip(); hits += ok
                fo.write(json.dumps({'corner': c, 'd1': d1, 'a': a, 'd2': d2, 'b': b, 'stand': [p['x'], p['z']], 'clip': ok}) + '\n'); fo.flush()
            e.load(tmp + '.b')
print('done part', PART, len(jobs), 'jobs', hits, 'clips')
