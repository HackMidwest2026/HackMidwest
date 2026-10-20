"""kpa_62 route A misses with hands off: run route A (lava on) with a mistake, press C-down (if any) and then release
every input; report where Mario ends up (riding or standing) and save that state for backup searches.
usage: kpa62_miss_spots.py STATE OUTDIR"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
st0, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kms%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2); place(e, -505.0, -20.0, y=35.0)
def hold(d, k, rel=20):
    for i in range(k): e.step(0, *CARD[d], 2)
    for i in range(rel): e.step(0, 0, 0, 2)
hold('right', 150, 30)
for f in range(50): e.step(0x80 if f < 25 else 0, *CARD['right'], 2)
for i in range(15): e.step(0, 0, 0, 2)
base = os.path.abspath(os.path.join(OUT, 'landed.st')); e.save(base)
cases = [('cdown%d' % T, 12, 12, T) for T in (31, 32, 33, 35, 36, 37, 38, 40)] + [('nocdown', 12, 12, 99)] + \
        [('run%d' % d, 12, d, 34) for d in (10, 11, 13, 14)] + [('left%d' % l, l, 12, 34) for l in (10, 13, 14)]
res = []
for name, L, D, T in cases:
    e.load(base)
    hold('up', 120, 10); hold('right', 30); hold('left', L); hold('down', D, 40)
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    for fr in range(1, T): e.step(0, *CARD['down'], 2)
    clipped = False
    if T < 99:
        e.step(0x400, *CARD['down'], 2)
    for i in range(150):                       # hands off
        e.step(0, 0, 0, 2); q = player(e); clipped |= inside_tower(q['x'], q['z']) and q['y'] > 40
    p = player(e); f = os.path.abspath(os.path.join(OUT, name + '.st')); e.save(f)
    r = {'case': name, 'pos': [round(p['x'], 2), round(p['y'], 2), round(p['z'], 2)], 'riding': p['action'] == 33, 'action': p['action'], 'clipped': clipped, 'state': f}
    res.append(r); print(r, flush=True)
json.dump(res, open(os.path.join(OUT, 'spots.json'), 'w'), indent=1)
