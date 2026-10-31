import sys, itertools, math, json
from emu import *
from pm import *
part, NP = int(sys.argv[1]), int(sys.argv[2])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jm_%d' % part)
AIR = (3, 4, 5, 6, 8, 15)
def go(tx, tz, maxf=200):
    for f in range(maxf):
        p = player(e); dx, dz = tx - p['x'], tz - p['z']; d = math.hypot(dx, dz)
        if d < 0.5: return
        mag = max(14, min(80, int(d * 10))); e.step(0, int(round(mag * dx / d)), int(round(-mag * dz / d)), 2)
e.load('states/pra01_ub_e3.st'); e.step(0, 0, 0, 2); go(550, -100)
B = '/dev/shm/pmbot/jm_%d_b.st' % part; e.save(B); e.step(0, 0, 0, 2)
seen = {}
starts = [(x, z) for x in (502, 505, 508, 512, 516) for z in (-72, -66, -60, -54, -48)][part::NP]
for sx, sz in starts:
    e.load(B); e.step(0, 0, 0, 2); go(550, sz)
    for f in range(120):
        if player(e)['x'] <= sx + 0.6 or where(e)[:2] != (21, 0): break
        e.step(0, -20, 0, 2)
    for i in range(8): e.step(0, 0, 0, 2)
    if where(e)[:2] != (21, 0): continue
    S0 = '/dev/shm/pmbot/jm_%d_s.st' % part; e.save(S0); e.step(0, 0, 0, 2)
    for m, h1, t1 in itertools.product((10, 20, 30, 40, 60, 80), (3, 5, 8), range(5, 13)):
        e.load(S0); e.step(0, 0, 0, 2); q = None
        for f in range(45):
            e.step(A if (f < h1 or t1 <= f < t1 + 2) else 0, -m, 0, 2); p = player(e)
            if where(e)[:2] != (21, 0): break
            if f > t1 and p['action'] not in AIR: q = p; break
        if not q or q['y'] < -50: continue
        key = (round(q['x'], 1), round(q['y'], 1), round(q['z'], 1))
        if key in seen: continue
        L = '/dev/shm/pmbot/jm_%d_l.st' % part; e.save(L)
        ok = []
        for w in range(6):
            e.load(L)
            for i in range(w): e.step(0, 0, 0, 2)
            if where(e)[:2] != (21, 0): break
            y0 = player(e)['y']; jumped = False
            for i in range(6):
                e.step(A, 0, 0, 2); p = player(e)
                if p['action'] == 3 and p['y'] > y0 + 8: jumped = True; break
            ok.append(jumped)
        seen[key] = dict(act=q['action'], ok=ok, src=(sx, sz, m, h1, t1))
json.dump([[list(k), v] for k, v in seen.items()], open('/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/jmap_%d.json' % part, 'w'))
print('JM part %d: %d distinct landings, %d jumpable' % (part, len(seen), sum(1 for v in seen.values() if any(v['ok']))), flush=True)
