"""Does a collision counter of -1 (the clippy state) change the kmr_11 Bush2 corner result? Same pinned starts and
alternating-stick sequences as kmr11_wiggle.py, run once with PlayerStatus+0x14 = 0 and once with -1 (written after
the start state loads; exploration). Counts runs that end behind the bush / over the void / through a wall.
usage: clippy_corner_test.py N"""
import math, os, random, sys
os.environ['ROOM'] = 'kmr11bush2'
from emu import *
from pm import *
from rooms import in_goal
from explore_clip import load_walls, crossed_wall
WALLS = load_walls()
e = Emu('pm-jp.z64', '/dev/shm/pmbot/clct')
def stick(deg, mag=80): r = math.radians(deg); return int(round(mag * math.cos(r))), int(round(-mag * math.sin(r)))
def setup(x, z, deg, frames, cnt):
    e.load('states/kmr11_e0_kingdone.st'); e.step(0, 0, 0, 2)
    e.w8(game_status(e) + 0x74, 1)
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, -8.0 if z > 25 else 0.0); e.wf32(PLAYER + PS_POS + 8, z)
    e.w8(PLAYER + 0x14, cnt & 0xFF)
    e.step(0, 0, 0, 12); s = stick(deg); e.step(0, s[0], s[1], 2 * frames); e.step(0, 0, 0, 4)
specs = [(-270, 80, a, 60) for a in (-40, -25, -12, 0, 15)] + [(-360, 10, a, 60) for a in (-20, -5, 0, 10)]
rng = random.Random(5)
seqs = [[(Z if rng.random() < .05 else 0,) + stick(rng.uniform(0, 360) if rng.random() < .4 else b + rng.gauss(0, 40)) for g in range(40)] for b in [rng.uniform(0, 360) for i in range(int(sys.argv[1]))]]
for cnt in (0, -1):
    hits = 0; n = 0; ex = None
    for i, sp in enumerate(specs):
        setup(*sp, cnt); st = '/dev/shm/pmbot/clct_%d.st' % i; e.save(st)
        for seq in seqs:
            e.load(st); p0 = player(e); why = None
            for (b, sx, sy) in seq:
                e.step(b, sx, sy, 2); p1 = player(e)
                if in_goal(p1['x'], p1['z']): why = 'goal'
                elif p1['y'] < -20: why = 'below'
                else:
                    w = crossed_wall(WALLS, (p0['x'], p0['z']), (p1['x'], p1['z']), min(p0['y'], p1['y']))
                    if w is not None: why = 'wall %d' % w
                if why: break
                p0 = p1
            n += 1
            if why: hits += 1; ex = ex or (sp, why, (round(p1['x'], 1), round(p1['y'], 1), round(p1['z'], 1)))
    print('counter', cnt, 'runs', n, 'hits', hits, 'example', ex, flush=True)
