"""kpa_62 universal backup after a missed remount (lava on): from every hands-off miss spot (still riding Laki), ride
half-tilt UP, RIGHT, UP (90 frames each) to the north-west corner, then either
  A) B, then route A's tail: hold UP, RIGHT, LEFT 12, run DOWN 12, mount, B, hold down, C-down on frame 34, or
  B) ride half-tilt D1 k1 (+ D2 k2) straight to the riding target, then B, hold down, C-down on frame 34.
Option B is searched from the corner point; option A is checked on every spot.
usage: kpa62_universal_backup.py SPOTS.json"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
HALF = {d: stick_for(a, 45) for d, a in (('right', 0), ('down', 90), ('left', 180), ('up', 270))}
VEC = {'right': (1, -1), 'down': (1, 1), 'left': (-1, 1), 'up': (-1, -1)}
spots = [s for s in json.load(open(sys.argv[1])) if s['riding']]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kub%d' % os.getpid())
tmp = '/dev/shm/pmbot/kub%d' % os.getpid()
def hold(d, k, rel=20, half=False):
    for i in range(k): e.step(0, *(HALF if half else CARD)[d], 2)
    for i in range(rel): e.step(0, 0, 0, 2)
def to_corner():
    for d in ('up', 'right', 'up'): hold(d, 90, 10, half=True)
def tail():
    e.step(0x40, 0, 0, 2)
    for fr in range(1, 34): e.step(0, *CARD['down'], 2)
    e.step(0x400, *CARD['down'], 2)
    for f in range(30):
        e.step(0, *CARD['down'], 2); q = player(e)
        if f > 18 and inside_tower(q['x'], q['z']) and q['y'] > 40: return True
    return False
okA = 0
for s in spots:
    e.load(s['state']); e.step(0, 0, 0, 2); to_corner()
    e.step(0x40, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    hold('up', 120, 10); hold('right', 30); hold('left', 12); hold('down', 12, 40)
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    ok = tail(); okA += ok
    print('A', s['case'], 'CLIP' if ok else 'miss', flush=True)
print('option A clips from', okA, 'of', len(spots), 'miss spots')
e.load(spots[0]['state']); e.step(0, 0, 0, 2); to_corner(); r0 = player(e); e.save(tmp + '.c')
print('corner riding point (%.3f %.3f)' % (r0['x'], r0['z']))
hits = []
for D1 in HALF:
    for D2 in [None] + [d for d in HALF if d != D1]:
        for k1 in range(1, 51):
            for k2 in ([0] if D2 is None else range(1, 51)):
                x = r0['x'] + 2.123 * (VEC[D1][0] * k1 + (VEC[D2][0] * k2 if D2 else 0))
                z = r0['z'] + 2.123 * (VEC[D1][1] * k1 + (VEC[D2][1] * k2 if D2 else 0))
                if abs(x + 442.17) > 1.0 or not (-63 <= z <= -40): continue
                e.load(tmp + '.c')
                for i in range(k1): e.step(0, *HALF[D1], 2)
                if D2:
                    for i in range(10): e.step(0, 0, 0, 2)
                    for i in range(k2): e.step(0, *HALF[D2], 2)
                for i in range(20): e.step(0, 0, 0, 2)
                q = player(e)
                if abs(q['x'] + 442.17) > 0.3: continue
                if tail(): hits.append(((D1, k1), (D2, k2), round(q['x'], 3), round(q['z'], 2)))
print('option B rides from the corner:', hits)
