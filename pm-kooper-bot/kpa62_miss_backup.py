"""kpa_62 backups from the hands-off miss spots (kpa62_miss_spots.py): Mario is still riding Laki, so ride at walking
speed (half tilt) in one or two cardinal segments to the riding target (x -442.17, z -61.4..-41.4), release, then B,
hold down, C-down on frame 34. Ride end points are predicted (2.123 units/axis/frame) and simulated when within 1 unit.
usage: kpa62_miss_backup.py SPOTS.json PART NPARTS OUT.jsonl"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
HALF = {d: stick_for(a, 45) for d, a in (('right', 0), ('down', 90), ('left', 180), ('up', 270))}
VEC = {'right': (1, -1), 'down': (1, 1), 'left': (-1, 1), 'up': (-1, -1)}
SP, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
spots = [s for s in json.load(open(SP)) if s['riding']][PART::NP]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kmb%d' % os.getpid())
def tail():
    e.step(0x40, 0, 0, 2)
    for fr in range(1, 34): e.step(0, *CARD['down'], 2)
    e.step(0x400, *CARD['down'], 2)
    for f in range(30):
        e.step(0, *CARD['down'], 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']) and q['y'] > 40: return True
    return False
fo = open(out, 'a')
for s in spots:
    e.load(s['state']); e.step(0, 0, 0, 2); r0 = player(e); hits = []
    for D1 in HALF:
        for D2 in [None] + [d for d in HALF if d != D1]:
            for k1 in range(1, 41):
                for k2 in ([0] if D2 is None else range(1, 41)):
                    x = r0['x'] + 2.123 * (VEC[D1][0] * k1 + (VEC[D2][0] * k2 if D2 else 0))
                    z = r0['z'] + 2.123 * (VEC[D1][1] * k1 + (VEC[D2][1] * k2 if D2 else 0))
                    if abs(x + 442.17) > 1.0 or not (-63 <= z <= -40): continue
                    e.load(s['state']); e.step(0, 0, 0, 2)
                    for i in range(k1): e.step(0, *HALF[D1], 2)
                    if D2:
                        for i in range(10): e.step(0, 0, 0, 2)
                        for i in range(k2): e.step(0, *HALF[D2], 2)
                    for i in range(20): e.step(0, 0, 0, 2)
                    q = player(e)
                    if abs(q['x'] + 442.17) > 0.3: continue
                    ok = tail()
                    rec = {'case': s['case'], 'ride': [[D1, k1], [D2, k2]], 'ridepos': [q['x'], q['z']], 'clip': ok}
                    fo.write(json.dumps(rec) + '\n'); fo.flush()
                    if ok: hits.append(rec['ride'])
    print(s['case'], 'from', s['pos'], '->', len(hits), 'clipping rides', hits[:6], flush=True)
