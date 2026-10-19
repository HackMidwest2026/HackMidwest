"""kpa_62: run the dismount / hold-down / remount sequence from a grid of ground positions and flag teleports.
For each start (x, z) on a y-0 floor: C-down (mount), ride 40 frames, C-down (dismount), wait W frames, then hold
DOWN and press C-down, hold down 30 more frames, release 15 frames. Every frame Mario's movement is tested against the
room's solid walls (explore_clip.crossed_wall); also flags ending on the lava pit / exit floors (11, 41) or a jump of
more than 30 units in one frame. usage: kpa62_remount_grid.py STATE PART NPARTS OUT.jsonl [STEP=20]
env FLOORS=20,23 limits the start grid to those floor colliders (at their own height)."""
import json, math, os, sys
os.environ.setdefault('ROOM', 'kpa62')
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from explore_clip import load_walls, crossed_wall
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
STEP = float(sys.argv[5]) if len(sys.argv) > 5 else 20
walls = load_walls()
C = json.load(open('kpa62_collision.json'))['colliders']
FLOOR_IDS = [int(v) for v in os.environ.get('FLOORS', '').split(',') if v]
floors = [t for c in C if not (c['flags'] & 0x7ffffe00 == 0x7ffffe00) and (c['id'] in FLOOR_IDS if FLOOR_IDS else True)
          for t in c['tris'] if t['n'][1] > 0.5 and (FLOOR_IDS or abs(t['v'][0][1]) < 1)]
def on_floor(x, z):
    """floor height under (x, z) among the chosen floors, or None"""
    for t in floors:
        (ax, _, az), (bx, _, bz), (cx, _, cz) = t['v']
        d = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
        if abs(d) < 1e-9: continue
        u = ((bz - cz) * (x - cx) + (cx - bx) * (z - cz)) / d; v = ((cz - az) * (x - cx) + (ax - cx) * (z - cz)) / d
        if u >= 0 and v >= 0 and u + v <= 1: return u * t['v'][0][1] + v * t['v'][1][1] + (1 - u - v) * t['v'][2][1]
    return None
pts = [(x, z, on_floor(x, z)) for x in [-700 + STEP * i for i in range(int(1300 / STEP))] for z in [-400 + STEP * j for j in range(int(1050 / STEP))] if on_floor(x, z) is not None]
pts = pts[PART::NP]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/k62g%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2); base = '/dev/shm/pmbot/k62g%d.st' % os.getpid(); e.save(base)
dn = stick_for(90, 80)
fo = open(out, 'a'); n = hits = 0
for (x, z, fy) in pts:
    for W in (3, 8, 14, 20, 30):
        e.load(base)
        e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, fy); e.wf32(PLAYER + PS_POS + 8, z)
        for i in range(8): e.step(0, 0, 0, 2)
        if abs(player(e)['y'] - fy) > 2: continue   # didn't stay on the chosen platform
        seq = [(0x400, 0, 0)] + [(0, 0, 0)] * 40 + [(0x400, 0, 0)] + [(0, 0, 0)] * W + [(0x400,) + dn] + [(0,) + dn] * 30 + [(0, 0, 0)] * 15
        p0 = player(e); why = None; trace = []
        for f, (b, sx, sy) in enumerate(seq):
            e.step(b, sx, sy, 2)
            if e.s16(GAME_MODE) != GM_WORLD: why = 'map change %s' % (where(e),); break
            p1 = player(e); trace.append((round(p1['x'], 1), round(p1['y'], 1), round(p1['z'], 1)))
            w = crossed_wall(walls, (p0['x'], p0['z']), (p1['x'], p1['z']), min(p0['y'], p1['y']))
            fl = e.s16(COLLISION + 2)
            if w is not None: why = 'crossed wall %d at frame %d' % (w, f)
            elif fl in (11, 41): why = 'on floor %d at frame %d' % (fl, f)
            elif math.hypot(p1['x'] - p0['x'], p1['z'] - p0['z']) > 30: why = 'jump %.0f at frame %d' % (math.hypot(p1['x'] - p0['x'], p1['z'] - p0['z']), f)
            if why: break
            p0 = p1
        n += 1
        if why:
            hits += 1; p = player(e)
            fo.write(json.dumps({'x': x, 'z': z, 'fy': fy, 'W': W, 'why': why, 'end': [p['x'], p['y'], p['z']], 'trace': trace[-12:]}) + '\n'); fo.flush()
print('done part', PART, len(pts), 'points', n, 'runs', hits, 'hits')
