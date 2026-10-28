"""Robustness of the RTA ending found by pra18_ns_rta.py (job: walk down n0, wait w, Z spin holding DOWN k frames,
jump (A held h) holding DOWN-RIGHT, hold DOWN m frames after landing, release, C-down). For each variation, finds the
frames on which C-down clips. usage: pra18_ns_rta_robust.py"""
import os, sys, json, math, itertools
sys.argv = ['x', '0', '1', '/dev/null']
os.environ['JOBS'] = '[]'
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_rta.py')).read().replace("print('done')", ''))
def cd_frames(job, start=None):
    if start:
        e.load(base)
        for f in range(40):
            q = player(e); dd = math.hypot(q['x'] - start[0], q['z'] - start[1])
            if dd < 0.6: break
            e.step(0, *st(math.degrees(math.atan2(start[1] - q['z'], start[0] - q['x'])), 80 if dd > 6 else 22), 2)
        for i in range(5): e.step(0, 0, 0, 2)
        if fstate() != 5: return 'laki left hover'
        e.save(alt)
    log, landed = play2(*job, b0state=alt if start else base)
    out = []
    for f, x, z, a, sp in log:
        if 560 <= x <= 580 and z > -24 and sp > 25:
            play2(*job, cd=f, b0state=alt if start else base)
            r = player(e)
            if r['action'] == 33 and r['z'] > 0: out.append((f, x, round(sp, 2)))
    return out
alt = '/dev/shm/pmbot/rb%d_alt.st' % os.getpid()
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_rta.py')).read()
def play2(n0, w, d1, k, h, d2, m, d3, cd=None, b0state=None):
    e.load(b0state); f = 0; log = []; landed = None
    for i in range(n0): e.step(0, *st(90, 80), 2); f += 1
    for i in range(w): e.step(0, 0, 0, 2); f += 1
    for i in range(k):
        b = Z if i == 0 else 0
        if cd == f: b |= D_CBUTTON
        e.step(b, *st(d1, 80), 2); f += 1
    for f2 in range(45):
        q = player(e)
        if landed is None and f2 > 2 and q['action'] in (0, 1, 2): landed = f2
        d = d2 if landed is None else (d3 if f2 - landed < m else None)
        s = st(d, 80) if d is not None else (0, 0)
        b = A if f2 < h else 0
        if cd == f: b |= D_CBUTTON
        e.step(b, *s, 2); q = player(e); log.append((f, round(q['x'], 2), round(q['z'], 2), q['action'], round(L()[2], 2))); f += 1
        if cd is not None and f > cd + 30: break
    return log, landed
REF = (1, 0, 90, 4, 6, 45, 5, 90)
print('REF', REF, cd_frames(REF), flush=True)
for i, name, vals in ((1, 'wait', (0, 1, 5, 10, 20, 40)), (0, 'down frames n0', (0, 1, 2, 3)), (3, 'spin frames k', (3, 4, 5)),
                      (4, 'A held h', (3, 4, 5, 6, 7, 8, 10)), (6, 'down after landing m', (3, 4, 5, 6, 7, 8, 10, 15, 30))):
    for v in vals:
        j = list(REF); j[i] = v
        print(name, v, cd_frames(tuple(j)), flush=True)
p = player(e)
e.load(base); p = player(e); print('push end mario (%.2f,%.2f)' % (p['x'], p['z']), flush=True)
for dx, dz in ((-3, 0), (-1.5, 0), (1.5, 0), (3, 0), (5, 0), (0, 1.5), (0, 3), (2, 2)):
    print('start offset', dx, dz, cd_frames(REF, start=(p['x'] + dx, p['z'] + dz)), flush=True)
