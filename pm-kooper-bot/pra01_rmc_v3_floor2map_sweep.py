import sys, itertools, math, json
from emu import *
from pm import *
part, NP = int(sys.argv[1]), int(sys.argv[2])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/f2_%d' % part)
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
TJ1 = [(510, -60, 40, 5, 10), (505, -60, 30, 5, 7), (505, -65, 20, 5, 10), (510, -65, 50, 5, 8), (515, -65, 70, 5, 8), (505, -55, 20, 5, 9)]
seen = {}
for sx, sz, m1, h1, t1 in TJ1[part::NP]:
    e.load('states/pra01_ub_e3.st'); e.step(0, 0, 0, 2); go(sx + 25, sz)
    for f in range(80):
        if player(e)['x'] <= sx: break
        e.step(0, -80, 0, 2)
    for i in range(9): e.step(0, 0, 0, 2)
    q = landing(45, lambda f: (A if (f < h1 or t1 <= f < t1 + 2) else 0, (-m1, 0)))
    if not q: continue
    for i in range(2): e.step(0, 0, 0, 2)
    L1 = '/dev/shm/pmbot/f2_%d_l1.st' % part; e.save(L1)
    for h2, t2, s2 in itertools.product((3, 4, 5, 6, 8), range(4, 11), ((0, 0), (-20, 0), (-40, 0), (-60, 0), (0, 40), (0, -40))):
        e.load(L1)
        q2 = landing(60, lambda f: (A if (f < h2 or t2 <= f < t2 + 2) else 0, s2))
        if not q2 or q2['y'] < 60: continue
        key = (round(q2['x'], 1), round(q2['y'], 1), round(q2['z'], 1))
        if key in seen: continue
        L2 = '/dev/shm/pmbot/f2_%d_l2.st' % part; e.save(L2)
        jump = []; clip = []
        for w in range(6):
            e.load(L2)
            for i in range(w): e.step(0, 0, 0, 2)
            if where(e)[:2] != (21, 0): jump.append(None); clip.append(None); continue
            y0 = player(e)['y']; j = False
            for i in range(6):
                e.step(A, 0, 0, 2); p = player(e)
                if p['action'] == 3 and p['y'] > y0 + 8: j = True; break
            jump.append(j)
            c = False
            for k3, m3 in itertools.product((0, 1, 2), (60, 80)):
                e.load(L2)
                for i in range(w): e.step(0, 0, 0, 2)
                for f in range(110):
                    e.step(A if f < 8 else 0, *((0, 0) if f < k3 else ((-int(m3 * .7071), -int(m3 * .7071)) if f < k3 + 8 else (0, -80))), 2)
                    if where(e)[:2] != (21, 0): break
                    if player(e)['z'] > 0.5: c = True; break
                if c: break
            clip.append(c)
        seen[key] = dict(act=q2['action'], jump=jump, clip=clip, src=(sx, sz, m1, h1, t1, h2, t2, s2))
json.dump([[list(k), v] for k, v in seen.items()], open('/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/f2map_%d.json' % part, 'w'))
print('F2 part %d: %d landings; jumpable %d; clip on 2+ consecutive frames %d' % (part, len(seen), sum(1 for v in seen.values() if any(v['jump'])),
      sum(1 for v in seen.values() if any(v['clip'][i] and v['clip'][i + 1] for i in range(5)))), flush=True)
