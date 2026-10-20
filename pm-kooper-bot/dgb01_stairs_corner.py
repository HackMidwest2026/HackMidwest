"""Acute corner on the debris slab where the plank wall (c45) meets the front broken-railing wall (z 99), around
(45.8, 250, 86). Tubba parked. Mario is walked into the corner, then for every stick angle (2 deg) and magnitude
tries: hold, jump+hold, jump+tornado+hold. Reports any run that ends west of the plank wall or below the walkway.
usage: dgb01_stairs_corner.py PART NPARTS OUT.jsonl"""
import json, math, sys
from emu import *
from pm import *

part, nparts, outp = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/corner%d' % part)
e.load('states/dgb01_e4_ctrl.st')
e.w8(PLAYER_DATA, 2)
for p in (1, 2, 3, 8): e.w8(PLAYER_DATA + 0x14 + 8 * p, 1)
tubba = [n for n in npcs(e) if n['id'] == 4][0]['addr']
def step(b, x, y, n=1):
    for i in range(n):
        e.wf32(tubba + 0x38, 0.0); e.wf32(tubba + 0x3C, -1000.0); e.wf32(tubba + 0x40, 0.0)
        e.step(b, x, y, 1)
def east(x, y, z): return 0.92 * x + 0.08 * y + 0.38 * z > 84.2
step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 80.0); e.wf32(PLAYER + PS_POS + 4, 270.0); e.wf32(PLAYER + PS_POS + 8, 60.0)
step(0, 0, 0, 30)
step(0, -56, -56, 40)          # walk down-left into the corner
step(0, 0, 0, 20)
print('corner start', player(e))
e.step(0, 0, 0, 1); start = '/dev/shm/pmbot/corner_start%d.st' % part; e.save(start)
f = open(outp, 'a')
angles = [a for a in range(0, 360, 2)][part::nparts]
for a in angles:
    for mag in (80, 60, 40, 25):
        sx, sy = round(mag * math.sin(math.radians(a))), round(mag * math.cos(math.radians(a)))
        for mode in ('hold', 'jump', 'tornado'):
            e.load(start)
            minx, low, west = 1e9, 1e9, False
            for i in range(120):
                b = 0
                if mode != 'hold' and 4 <= i < 26: b = A
                if mode == 'tornado' and 30 <= i < 32: b = A
                step(b, sx, sy)
                p = player(e)
                low = min(low, p['y'])
                if not east(p['x'], p['y'], p['z']): west = True
            p = player(e)
            r = {'a': a, 'mag': mag, 'stick': (sx, sy), 'mode': mode, 'end': (round(p['x'], 2), round(p['y'], 2), round(p['z'], 2)),
                 'low': round(low, 1), 'west': west}
            f.write(json.dumps(r) + '\n')
            if west or low < 200: print('HIT', r, flush=True)
    f.flush()
print('done part', part)
