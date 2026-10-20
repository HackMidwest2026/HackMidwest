"""kpa_62: setups with a single exact count. Forgiving ledge jump (kpa62_landings.py) -> up to two long cardinal holds
(on foot, 70 frames each; kept only if the spot is the same after 90 frames, i.e. pinned) -> 0..8 mount/dismount
cycles (C-down, ride 25, B, wait 30; countable, no timing) -> ONE exact segment: either a
full-tilt walk (cardinal, k frames) or, after mounting, a half-tilt ride (cardinal, k frames) -> clip (mount if not
riding, ride 40, B, hold down, C-down on frame 34). Records every clip; the exact segment is the only counted input.
usage: kpa62_onexact.py STATE LANDINGS.json PART NPARTS OUT.jsonl"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
HALF = {d: stick_for(a, 45) for d, a in (('right', 0), ('down', 90), ('left', 180), ('up', 270))}
VEC = {'right': (1, -1), 'down': (1, 1), 'left': (-1, 1), 'up': (-1, -1)}
st0, LJ, PART, NP, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/koe%d' % os.getpid())
tmp = '/dev/shm/pmbot/koe%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); place(e, -505.0, -20.0, y=35.0)
for i in range(150): e.step(0, *CARD['right'], 2)
for i in range(30): e.step(0, 0, 0, 2)
e.save(tmp + '.fp')
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
def tail(riding):
    if not riding:
        for i in range(40): e.step(0, 0, 0, 2)
        e.step(0x400, 0, 0, 2)
        for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    for fr in range(1, 34): e.step(0, *CARD['down'], 2)
    e.step(0x400, *CARD['down'], 2)
    for f in range(30):
        e.step(0, *CARD['down'], 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']): return True
    return False
holds = [()] + [(a,) for a in CARD] + [(a, b) for a in CARD for b in CARD if b != a] + [('up', 'right', 'left')]
jobs = [(lk, h) for lk in lands for h in holds][PART::NP]
fo = open(out, 'a'); hits = 0; sims = 0; seen = set()
for (lk, h) in jobs:
    jump(lands[lk]); okpin = True
    for d in h:
        for i in range(70): e.step(0, *CARD[d], 2)
        a = player(e)
        for i in range(20): e.step(0, *CARD[d], 2)
        b = player(e)
        if abs(a['x'] - b['x']) > .01 or abs(a['z'] - b['z']) > .01: okpin = False; break
    for i in range(20): e.step(0, 0, 0, 2)
    p = player(e)
    if not okpin or abs(p['y'] - 60) > .5: continue
    key = (round(p['x'], 2), round(p['z'], 2))
    if key in seen: continue
    seen.add(key); e.save(tmp + '.p0')
    for c in range(0, 9):
        e.load(tmp + '.p0')
        for cc in range(c):
            e.step(0x400, 0, 0, 2)
            for i in range(25): e.step(0, 0, 0, 2)
            e.step(0x40, 0, 0, 2)
            for i in range(30): e.step(0, 0, 0, 2)
        p = player(e)
        if abs(p['y'] - 60) > .5: break
        src = tmp + ('.p' if c else '.p0')   # a save right after a load fails, so c = 0 reuses .p0
        if c: e.save(src)
        # exact walk
        for W in CARD:
            for k in range(1, 30):
                x = p['x'] + 3.215 * VEC[W][0] * k; z = p['z'] + 3.215 * VEC[W][1] * k
                if abs(x + 440.69) > 0.6 or not (-61 <= z <= -39): continue
                e.load(src); sims += 1
                for i in range(k): e.step(0, *CARD[W], 2)
                for i in range(20): e.step(0, 0, 0, 2)
                ok = tail(False); hits += ok; q = player(e)
                rec = {'jump': lands[lk], 'holds': h, 'cycles': c, 'pin': [p['x'], p['z']], 'exact': ['walk', W, k], 'clip': ok}
                fo.write(json.dumps(rec) + '\n'); fo.flush()
                if ok: print(rec, flush=True)
        # exact half-tilt ride
        e.load(src)
        for i in range(40): e.step(0, 0, 0, 2)
        e.step(0x400, 0, 0, 2)
        for i in range(30): e.step(0, 0, 0, 2)
        r0 = player(e); e.save(tmp + '.m')
        for W in CARD:
            for k in range(1, 45):
                x = r0['x'] + 2.123 * VEC[W][0] * k; z = r0['z'] + 2.123 * VEC[W][1] * k
                if abs(x + 442.17) > 0.8 or not (-63 <= z <= -39): continue
                e.load(tmp + '.m'); sims += 1
                for i in range(k): e.step(0, *HALF[W], 2)
                for i in range(20): e.step(0, 0, 0, 2)
                ok = tail(True); hits += ok
                rec = {'jump': lands[lk], 'holds': h, 'cycles': c, 'pin': [p['x'], p['z']], 'exact': ['ride', W, k], 'clip': ok}
                fo.write(json.dumps(rec) + '\n'); fo.flush()
                if ok: print(rec, flush=True)
print('done part', PART, len(jobs), 'jobs', len(seen), 'pins', sims, 'sims', hits, 'clips')
