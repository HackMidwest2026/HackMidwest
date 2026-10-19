"""kpa_62 (outside Bowser's Castle, the y-60 platform right of / below the Deep Focus platform): find where the
dismount / hold-down / remount sequence teleports Mario into the right wall, from positions Mario can really reach.
Start: Mario placed at a known-good spot on the platform (SEED), then walks at angle A for K frames (stops at walls) ->
start position. Then: C-down (mount), ride 40 frames, C-down (dismount), wait W frames, hold DOWN + C-down, hold down 30
frames, release 15. Flags any frame where Mario's movement crosses a solid wall (explore_clip.crossed_wall).
usage: kpa62_remount_walk.py STATE PART NPARTS OUT.jsonl [SEEDX SEEDZ SEEDY]
env: XMIN (skip starts west of it), DMS (dismount buttons), TOWER_GOAL=1 (hit = Mario ends inside the
tower outline (collider 1) instead of any wall crossing), WAITS (frames after dismount), HOLDS (frames of holding down before the
remount C-down), ASTEP (walk angle step). Each combination is run with both dismount buttons (B, C-down)."""
import json, math, os, sys
os.environ.setdefault('ROOM', 'kpa62')
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from explore_clip import load_walls, crossed_wall
st0, PART, NP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
SX, SZ, SY = (float(v) for v in sys.argv[5:8]) if len(sys.argv) > 7 else (-460.0, -60.0, 60.0)
walls = load_walls()
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/k62w%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, SX); e.wf32(PLAYER + PS_POS + 4, SY); e.wf32(PLAYER + PS_POS + 8, SZ)
for i in range(20): e.step(0, 0, 0, 2)
seedp = player(e); base = '/dev/shm/pmbot/k62w%d.st' % os.getpid(); e.save(base)
dn = stick_for(90, 80)
XMIN = float(os.environ.get('XMIN', '-1e9'))
DMS = [int(v, 0) for v in os.environ.get('DMS', '0x40,0x400').split(',')]
TOWER_GOAL = bool(os.environ.get('TOWER_GOAL'))
TOWER = [(-365, -5), (-394, -29), (-409, -55), (-414, -75), (-415, -96), (-408, -108), (-390, -112), (-376, -103),
         (-357, -79), (-341, -48), (-340, -20), (-348, -4)]
def inside_tower(x, z, poly=TOWER):
    c = False
    for (x0, z0), (x1, z1) in zip(poly, poly[1:] + poly[:1]):
        if (z0 > z) != (z1 > z) and x < x0 + (z - z0) * (x1 - x0) / (z1 - z0): c = not c
    return c
WAITS = [int(v) for v in os.environ.get('WAITS', '3,8,14,20,30').split(',')]
HOLDS = [int(v) for v in os.environ.get('HOLDS', '0').split(',')]
walks = [(a, k) for a in range(0, 360, int(os.environ.get('ASTEP', '10'))) for k in range(2, 42, 2)][PART::NP]
fo = open(out, 'a'); n = hits = 0; seen = set()
for (a, k) in walks:
    e.load(base)
    for i in range(k): e.step(0, *stick_for(a, 80), 2)
    for i in range(6): e.step(0, 0, 0, 2)
    p = player(e)
    cell = (round(p['x']), round(p['z']))
    if cell in seen or abs(p['y'] - SY) > 2: continue
    seen.add(cell)
    e.save(base + '.w')
    if p['x'] < XMIN: continue
    for DM, W, H in [(dm, w, h) for dm in DMS for w in WAITS for h in HOLDS]:
        e.load(base + '.w')
        seq = [(0x400, 0, 0)] + [(0, 0, 0)] * 40 + [(DM, 0, 0)] + [(0, 0, 0)] * W + [(0,) + dn] * H + [(0x400,) + dn] + [(0,) + dn] * 25 + [(0, 0, 0)] * 10
        p0 = player(e); why = None; trace = []
        for f, (b, sx, sy) in enumerate(seq):
            e.step(b, sx, sy, 2)
            if e.s16(GAME_MODE) != GM_WORLD: why = 'map change'; break
            p1 = player(e); trace.append((round(p1['x'], 1), round(p1['y'], 1), round(p1['z'], 1)))
            if TOWER_GOAL:
                if f > len(seq) - 12 and inside_tower(p1['x'], p1['z']): why = 'inside tower at frame %d' % f; break
            else:
                w = crossed_wall(walls, (p0['x'], p0['z']), (p1['x'], p1['z']), min(p0['y'], p1['y']))
                if w is not None: why = 'crossed wall %d at frame %d' % (w, f); break
            p0 = p1
        n += 1
        if why:
            hits += 1; q = player(e)
            fo.write(json.dumps({'walk': [a, k], 'start': [p['x'], p['y'], p['z']], 'W': W, 'H': H, 'DM': DM, 'why': why, 'end': [q['x'], q['y'], q['z']], 'trace': trace[-10:]}) + '\n'); fo.flush()
print('done part', PART, len(seen), 'start positions', n, 'runs', hits, 'hits')
