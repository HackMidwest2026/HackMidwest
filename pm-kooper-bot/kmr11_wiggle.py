"""Stick-wiggle search at the trapped arena's Bush2 corner (kmr_11 right after the Goomba King; Goombario, normal
boots, normal spin, no badges). From pinned start states (Mario walked into the acute corner (-227, 48.5) from
several angles, and into the bush tip / fortress gap at (-309, 19)), runs
  1. systematic: alternate two stick angles every 1 or 2 game frames for 40 frames, every angle pair at 6 degrees,
     plain or after a spin (Z) on frame 0;
  2. random: per-frame random stick angle/magnitude with random Z / A / B presses, until MINUTES run out.
A hit is any frame where Mario is behind the bush / over the void (rooms.py kmr11bush2 goal), below y -20, or
crosses a wall (explore_clip.crossed_wall). usage: kmr11_wiggle.py PART NPARTS MINUTES OUT.jsonl"""
import json, math, os, random, sys, time
os.environ['ROOM'] = 'kmr11bush2'
from emu import *
from pm import *
from rooms import in_goal
from explore_clip import load_walls, crossed_wall

part, nparts, minutes, outp = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
t_end = time.time() + 60 * minutes
WALLS = load_walls()
e = Emu('pm-jp.z64', '/dev/shm/pmbot/wig%d' % part)
def stick(deg, mag): r = math.radians(deg); return int(round(mag * math.cos(r))), int(round(-mag * math.sin(r)))
def pinned(x, z, deg, frames=60):
    e.load('states/kmr11_e0_kingdone.st'); e.step(0, 0, 0, 2)
    e.w8(game_status(e) + 0x74, 1)
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, -8.0 if z > 25 else 0.0); e.wf32(PLAYER + PS_POS + 8, z)
    e.step(0, 0, 0, 12)
    s = stick(deg, 80)
    e.step(0, s[0], s[1], 2 * frames)
    e.step(0, 0, 0, 4)
# pinned starts: into the acute corner from the pocket, and into the bush tip / fortress gap from the west strip
specs = [(-270, 80, a) for a in (-40, -25, -12, 0, 15)] + [(-255, 60, a) for a in (-20, 0, 20)] + \
        [(-360, 10, a) for a in (-20, -5, 0, 10)]
specs = [(x, z, a, 60) for x, z, a in specs] + [(-335, 4, a, k) for a in (-30, -15, -5) for k in (8, 14)]
starts = []
for i, (x, z, a, k) in enumerate(specs):
    pinned(x, z, a, k)
    p = player(e)
    path = '/dev/shm/pmbot/wig%d_s%d.st' % (part, i)
    e.save(path)
    starts.append((path, (p['x'], p['y'], p['z']), 'from (%d,%d) holding %d deg %d frames' % (x, z, a, k)))
f = open(outp, 'a')
def run(start, seq):
    """seq: list of (buttons, sx, sy) per game frame; returns hit dict or None and the closest-to-goal point"""
    e.load(start[0])
    p0 = player(e)
    for i, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        p1 = player(e)
        why = None
        if in_goal(p1['x'], p1['z']): why = 'behind bush / over void'
        elif p1['y'] < -20: why = 'below floor'
        else:
            w = crossed_wall(WALLS, (p0['x'], p0['z']), (p1['x'], p1['z']), min(p0['y'], p1['y']))
            if w is not None: why = 'crossed wall %d' % w
        if why: return {'why': why, 'frame': i, 'pos': (p1['x'], p1['y'], p1['z'])}
        p0 = p1
    return None
n, hits, maxx = 0, 0, -1e9
pairs = [(a1, a2) for a1 in range(0, 360, 6) for a2 in range(0, 360, 6) if a1 < a2]
jobs = [(si, a1, a2, per, spin) for si in range(len(starts)) for (a1, a2) in pairs for per in (1, 2) for spin in (0, 1)]
for j in jobs[part::nparts]:
    if time.time() > t_end: break
    si, a1, a2, per, spin = j
    seq = []
    for g in range(40):
        a = a1 if (g // per) % 2 == 0 else a2
        seq.append(((Z if spin and g == 0 else 0),) + stick(a, 80))
    h = run(starts[si], seq)
    n += 1; maxx = max(maxx, player(e)['x'])
    if h:
        hits += 1; rec = {'kind': 'alt', 'start': starts[si][2], 'a1': a1, 'a2': a2, 'per': per, 'spin': spin, **h}
        f.write(json.dumps(rec) + '\n'); f.flush(); print('HIT', rec, flush=True)
print('part %d systematic done: %d runs, %d hits, max x %.2f' % (part, n, hits, maxx), flush=True)
rng = random.Random(1000 + part)
nr = 0
while time.time() < t_end:
    si = rng.randrange(len(starts))
    seq = []
    base = rng.uniform(0, 360)
    for g in range(rng.choice((20, 40, 60))):
        mode = rng.random()
        a = base + rng.gauss(0, 40) if mode < 0.6 else rng.uniform(0, 360)
        mag = rng.choice((80, 80, 60, 40, 20, 10))
        r = rng.random()
        b = Z if r < 0.04 else A if r < 0.08 else B if r < 0.10 else 0
        seq.append((b,) + stick(a, mag))
    h = run(starts[si], seq)
    nr += 1; maxx = max(maxx, player(e)['x'])
    if h:
        hits += 1; rec = {'kind': 'random', 'start': starts[si][2], 'seq': seq, **h}
        f.write(json.dumps(rec) + '\n'); f.flush(); print('HIT', {k: v for k, v in rec.items() if k != 'seq'}, flush=True)
    if nr % 2000 == 0: print('part %d random %d runs, %d hits total, max x %.2f' % (part, nr, hits, maxx), flush=True)
print('done part %d: %d systematic + %d random runs, %d hits, max x %.2f' % (part, n, nr, hits, maxx), flush=True)
print('starts', [(s[2], [round(v, 2) for v in s[1]]) for s in starts], flush=True)
