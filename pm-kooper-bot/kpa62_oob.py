"""kpa_62: out-of-bounds clip in the top-right (screen) corner of the y-60 platform, where the tower's west face meets
the castle wall. From a start spot (Laki settled), hold stick angle A1 for N1 frames (into the corner), then angle A2;
every frame checks whether Mario crossed a solid wall (explore_clip.crossed_wall) or stands inside the tower / behind
the castle wall. Stick angles: 270 up, 0 right, 90 down, 180 left.
usage: kpa62_oob.py STATE PART NPARTS OUT.jsonl   env: STEP (angle step, 5), N1S (40), K2 (60), MAG (80), STARTS (x,z;...), A1S, A2S (angle ranges lo,hi)"""
import json, os, sys
os.environ.setdefault('ROOM', 'kpa62')
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from explore_clip import load_walls, crossed_wall
from kpa62_tower import inside_tower
from kpa62_place import place
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
STEP = int(os.environ.get('STEP', '5')); N1S = [int(v) for v in os.environ.get('N1S', '40').split(',')]
K2 = int(os.environ.get('K2', '60')); MAG = int(os.environ.get('MAG', '80'))
SOLID = {0, 1, 4, 12, 21}            # castle walls, tower, raised platforms (cliff edges of the floors don't count)
walls = [w for w in load_walls() if w[0] in SOLID]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/koo%d' % os.getpid())
tmp = '/dev/shm/pmbot/koo%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2)
STARTS = [tuple(int(v) for v in s.split(',')) for s in os.environ['STARTS'].split(';')] if os.environ.get('STARTS') else [(-450, -70), (-440, -95), (-460, -95)]
for i, s in enumerate(STARTS):
    e.load(st0); e.step(0, 0, 0, 2); place(e, float(s[0]), float(s[1])); e.save(tmp + '.s%d' % i)
def oob(p): return inside_tower(p['x'], p['z']) or (p['z'] < -103 and -427 < p['x'] < -388)
A1S = [int(v) for v in os.environ.get('A1S', '0,360').split(',')]; A2S = [int(v) for v in os.environ.get('A2S', '0,360').split(',')]
jobs = [(i, a1, n1) for i in range(len(STARTS)) for a1 in range(A1S[0], A1S[1], STEP) for n1 in N1S][PART::NP]
fo = open(out, 'a'); hits = 0
for (i, a1, n1) in jobs:
    e.load(tmp + '.s%d' % i)
    for k in range(n1): e.step(0, *stick_for(a1, MAG), 2)
    c = player(e)
    if abs(c['y'] - 60) > .5: continue
    e.save(tmp + '.c')
    for a2 in range(A2S[0], A2S[1], STEP):
        e.load(tmp + '.c'); p0 = player(e); why = None
        for k in range(K2):
            e.step(0, *stick_for(a2, MAG), 2); p1 = player(e)
            w = crossed_wall(walls, (p0['x'], p0['z']), (p1['x'], p1['z']), min(p0['y'], p1['y']))
            if w is not None or oob(p1): why = ('crossed wall %d' % w if w is not None else 'oob position', k + 1); break
            p0 = p1
        if why:
            hits += 1
            rec = {'start': STARTS[i], 'A1': a1, 'N1': n1, 'corner': [c['x'], c['z']], 'A2': a2, 'why': why[0], 'frame': why[1], 'at': [p1['x'], p1['y'], p1['z']]}
            fo.write(json.dumps(rec) + '\n'); fo.flush()
print('done part', PART, len(jobs), 'jobs', hits, 'hits')
