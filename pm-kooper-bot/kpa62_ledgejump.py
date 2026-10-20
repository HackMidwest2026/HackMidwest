"""kpa_62: one jump from the pinned y-35 ledge spot that lands directly on the clip line (no spin, cardinals only).
Jump: A held a frames (25 = full, 8 = short); in the air hold cardinal D1 for d1 frames from takeoff, then cardinal D2
for d2 frames, then neutral. Landing spots on the y-60 platform within the line (x -440.80..-440.58, z -60..-40) get
the clip check; Mario's facing is whatever the inputs left it (a LEFT input in the air turns him left).
usage: kpa62_ledgejump.py STATE PART NPARTS OUT.jsonl"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/klj%d' % os.getpid())
tmp = '/dev/shm/pmbot/klj%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); place(e, -505.0, -20.0, y=35.0)
for i in range(150): e.step(0, *CARD['right'], 2)
for i in range(30): e.step(0, 0, 0, 2)
e.save(tmp + '.fp')
def clip():
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
jobs = [(a, D1, d1) for a in (25, 8) for D1 in CARD for d1 in range(0, 40)][PART::NP]
fo = open(out, 'a'); n = near = hits = 0
for (a, D1, d1) in jobs:
    for D2 in [None] + [d for d in CARD if d != D1]:
        for d2 in ([0] if D2 is None else range(1, 31)):
            e.load(tmp + '.fp')
            for f in range(60):
                st = CARD[D1] if f < d1 else (CARD[D2] if D2 and f < d1 + d2 else (0, 0))
                e.step(0x80 if f < a else 0, *st, 2)
            for i in range(10): e.step(0, 0, 0, 2)
            p = player(e); n += 1
            if abs(p['y'] - 60) > .5: continue
            rec = {'a': a, 'D1': D1, 'd1': d1, 'D2': D2, 'd2': d2, 'land': [p['x'], p['z']]}
            if -441.5 <= p['x'] <= -440.0 and -61 <= p['z'] <= -39:
                near += 1
                rec['clip'] = clip() if (-440.80 <= p['x'] <= -440.58 and -60 <= p['z'] <= -40) else None
                hits += bool(rec['clip'])
                if rec['clip']: print(rec, flush=True)
            fo.write(json.dumps(rec) + '\n')
print('done part', PART, n, 'jumps', near, 'near the line', hits, 'clips')
