"""pra_18 north->south RIGHT SIDE, RTA ending with NO spin and NO diagonals (right / down / A only).
Base: pra18_ns_rta.py ALIGN state (push done, Mario held LEFT into the wall corner at x 513.00). Then:
walk RIGHT r frames, walk DOWN dn frames, jump 1 (A held 6) holding s1, optional jump 2 (after g frames of
running DOWN after landing, or none) holding s2, then hold DOWN. While Mario is above Laki his speed is capped at 6.
C-down is tried on frames where Laki's speed is in the clip window. usage: pra18_ns_nospin.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
MYARGS = list(sys.argv)
sys.argv = ['x', '0', '1', '/dev/null']
os.environ['JOBS'] = '[]'; os.environ['ALIGN'] = '1'
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_rta.py')).read().replace("print('done')", ''))
part, nparts, out = int(MYARGS[1]), int(MYARGS[2]), MYARGS[3]
def play(r, dn, s1, g, s2, cd=None):
    e.load(base); f = 0; log = []
    plan = [(0, 0)] * r + [(0, 90)] * dn
    for b, d in plan:
        if cd == f: b |= D_CBUTTON
        e.step(b, *st(d, 80), 2); f += 1
    phase = 1; jt = 0; ground = 0
    for i in range(70):
        q = player(e); grounded = q['action'] in (0, 1, 2)
        if phase == 1:
            b = A if jt < 6 else 0; d = s1; jt += 1
            if jt > 3 and grounded: phase = 2; ground = 0
        if phase == 2:
            if g is not None and ground == g: phase = 3; jt = 0
            else: b, d = 0, 90; ground += 1
        if phase == 3:
            b = A if jt < 6 else 0; d = s2; jt += 1
            if jt > 3 and grounded: phase = 4
        if phase == 4: b, d = 0, 90
        if cd == f: b |= D_CBUTTON
        e.step(b, *st(d, 80), 2); q = player(e); log.append((f, round(q['x'], 2), round(q['z'], 2), q['action'], round(L()[2], 2))); f += 1
        if cd is not None and f > cd + 30: break
    return log
jobs = list(itertools.product(range(0, 21), range(0, 17), (90, 0), (None, 0, 1, 2, 3, 4, 6, 8), (90, 0)))
jobs = [j for j in jobs if not (j[3] is None and j[4] == 0)][part::nparts]
fo = open(out, 'a')
for job in jobs:
    log = play(*job)
    cands = [(f, x, z, a, sp) for f, x, z, a, sp in log if 566 <= x <= 576 and -22 <= z <= -12 and a in (0, 1, 2) and sp > 30]
    near = min(cands, key=lambda c: abs(c[4] - (616 - c[1])), default=None)
    hits = []
    for f, x, z, a, sp in cands:
        if 616 - x - 1.5 <= sp <= 616 - x + 0.6:
            play(*job, cd=f)
            if player(e)['action'] == 33 and player(e)['z'] > 0: hits.append((f, x, z, sp))
    rec = {'job': job, 'near': near, 'end': log[-1][1:3], 'clips': hits}
    print(('CLIP ' if hits else '') + json.dumps(rec), flush=True)
    if hits: fo.write(json.dumps(rec) + '\n'); fo.flush()
print('done')
