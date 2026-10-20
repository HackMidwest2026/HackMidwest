"""kpa_62: forgiving ledge jump (from kpa62_landings.py) -> optional walk (cardinal, full tilt, k0 frames) -> settle ->
mount -> ride Laki at walking speed (half tilt, magnitude MAG) in one or two cardinal segments -> release -> B -> hold
down -> C-down on frame 34. Ride end points are predicted from an open-ground displacement table and simulated when
within 1 unit of the clip line (ride x -442.17 +- 0.2); every simulated program's result is recorded.
usage: kpa62_ridewalk.py STATE LANDINGS.json PART NPARTS OUT.jsonl   env: MAG (default 45)"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
MAG = int(os.environ.get('MAG', '45'))
HALF = {d: stick_for(a, MAG) for d, a in (('right', 0), ('down', 90), ('left', 180), ('up', 270))}
VEC = {'right': (1, -1), 'down': (1, 1), 'left': (-1, 1), 'up': (-1, -1)}
st0, LJ, PART, NP, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/krw%d' % os.getpid())
tmp = '/dev/shm/pmbot/krw%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); place(e, -505.0, -20.0, y=35.0)
for i in range(150): e.step(0, *CARD['right'], 2)
for i in range(30): e.step(0, 0, 0, 2)
e.save(tmp + '.fp')
# distinct landings, one representative program each (middle of its d window)
lands = {}
for r in json.load(open(LJ)):
    key = tuple(r['land'])
    if key not in lands or r['d'][1] - r['d'][0] > lands[key]['d'][1] - lands[key]['d'][0]: lands[key] = r
def jump(r):
    e.load(tmp + '.fp')
    if r['spin']:
        e.step(0x20, *CARD[r['spin'][0]], 2)
        for i in range(r['spin'][1] - 1): e.step(0, *CARD[r['spin'][0]], 2)
    d = (r['d'][0] + r['d'][1]) // 2
    for f in range(50): e.step(0x80 if f < r['a'] else 0, *(CARD['right'] if f < d else (0, 0)), 2)
    for i in range(15): e.step(0, 0, 0, 2)
def clip():
    e.step(0x40, 0, 0, 2)
    for fr in range(1, 34): e.step(0, *CARD['down'], 2)
    e.step(0x400, *CARD['down'], 2)
    for f in range(30):
        e.step(0, *CARD['down'], 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']): return True
    return False
STEP = 2.123
fo = open(out, 'a'); hits = 0; sims = 0
jobs = [(k, W0, k0) for k in lands for W0 in [None] + list(CARD) for k0 in ([0] if W0 is None else range(1, 13))][PART::NP]
for (lk, W0, k0) in jobs:
    jump(lands[lk])
    if W0:
        for i in range(k0): e.step(0, *CARD[W0], 2)
        for i in range(20): e.step(0, 0, 0, 2)
    p = player(e)
    if abs(p['y'] - 60) > .5: continue
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x400, 0, 0, 2)
    for i in range(30): e.step(0, 0, 0, 2)
    r0 = player(e); e.save(tmp + '.m')
    for D1 in CARD:
        for D2 in [None] + [d for d in CARD if d != D1]:
            for k1 in range(1, 41):
                for k2 in ([0] if D2 is None else range(1, 41)):
                    x = r0['x'] + STEP * (VEC[D1][0] * k1 + (VEC[D2][0] * k2 if D2 else 0))
                    z = r0['z'] + STEP * (VEC[D1][1] * k1 + (VEC[D2][1] * k2 if D2 else 0))
                    if abs(x + 442.17) > 1.0 or not (-62 <= z <= -40): continue
                    e.load(tmp + '.m'); sims += 1
                    for i in range(k1): e.step(0, *HALF[D1], 2)
                    if D2:
                        for i in range(10): e.step(0, 0, 0, 2)
                        for i in range(k2): e.step(0, *HALF[D2], 2)
                    for i in range(20): e.step(0, 0, 0, 2)
                    q = player(e)
                    if abs(q['x'] + 442.17) > 0.25: continue
                    ok = clip(); hits += ok
                    rec = {'jump': lands[lk], 'walk': [W0, k0], 'ride': [[D1, k1], [D2, k2]], 'ridepos': [q['x'], q['z']], 'clip': ok}
                    fo.write(json.dumps(rec) + '\n'); fo.flush()
                    if ok: print(rec, flush=True)
print('done part', PART, len(jobs), 'jobs', sims, 'sims', hits, 'clips')
