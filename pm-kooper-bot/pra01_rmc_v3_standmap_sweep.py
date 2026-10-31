import sys, itertools, math, json
from emu import *
from pm import *
part, NP = int(sys.argv[1]), int(sys.argv[2])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/vm_%d' % part)
AIR = (3, 4, 5, 6, 8, 15)
def go(tx, tz, maxf=200):
    for f in range(maxf):
        p = player(e); dx, dz = tx - p['x'], tz - p['z']; d = math.hypot(dx, dz)
        if d < 0.5: return
        mag = max(14, min(80, int(d * 10))); e.step(0, int(round(mag * dx / d)), int(round(-mag * dz / d)), 2)
def landing(maxf, inp):
    for f in range(maxf):
        b, s = inp(f); e.step(b, *s, 2); p = player(e)
        if where(e)[:2] != (21, 0): return None
        if f > 3 and p['action'] not in AIR: return p
    return None
def rest():
    for i in range(2): e.step(0, 0, 0, 2)
    q2 = landing(60, lambda f: (A if (f < 5 or 6 <= f < 8) else 0, (0, 0)))
    if not q2 or q2['y'] < 85: return False
    for i in range(2): e.step(0, 0, 0, 2)
    S = '/dev/shm/pmbot/vm_%d_j.st' % part; e.save(S)
    for k3 in (0, 1, 2):
        e.load(S)
        for f in range(110):
            e.step(A if f < 8 else 0, *((0, 0) if f < k3 else ((-56, -56) if f < k3 + 8 else (0, -80))), 2)
            if where(e)[:2] != (21, 0): break
            if player(e)['z'] > 0.5: return True
    return False
e.load('states/pra01_ub_e3.st'); e.step(0, 0, 0, 2); go(550, -100)
B = '/dev/shm/pmbot/vm_%d_b.st' % part; e.save(B); e.step(0, 0, 0, 2)
cells = [(x, z) for x in [500 + 1.5 * i for i in range(22)] for z in [-74 + 1.5 * j for j in range(19)]][part::NP]
out = []
for x, z in cells:
    e.load(B); e.step(0, 0, 0, 2); go(550, z)
    ok = abs(player(e)['z'] - z) < 1
    for f in range(120):
        p = player(e)
        if p['x'] <= x + 0.6 or where(e)[:2] != (21, 0): break
        e.step(0, -20, 0, 2)
    for i in range(8): e.step(0, 0, 0, 2)
    p = player(e)
    if where(e)[:2] != (21, 0) or not ok or abs(p['x'] - x) > 1.2 or abs(p['z'] - z) > 1.2:
        out.append((x, z, None)); continue
    S0 = '/dev/shm/pmbot/vm_%d_s.st' % part; e.save(S0); e.step(0, 0, 0, 2)
    wins = []
    for m, t1 in itertools.product((20, 30, 40, 60, 80), range(6, 12)):
        e.load(S0); e.step(0, 0, 0, 2)
        q = landing(45, lambda f: (A if (f < 5 or t1 <= f < t1 + 2) else 0, (0, 0) if f < 1 else (-m, 0)))
        if q and q['y'] > -5 and rest(): wins.append((m, t1))
    out.append((round(p['x'], 2), round(p['z'], 2), wins))
json.dump(out, open('/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/vmap_%d.json' % part, 'w'))
print('VM part %d: %d cells, %d reachable, %d working' % (part, len(out), sum(1 for o in out if o[2] is not None), sum(1 for o in out if o[2])), flush=True)
