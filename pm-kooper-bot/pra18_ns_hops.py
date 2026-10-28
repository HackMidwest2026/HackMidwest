"""pra_18 north->south RIGHT SIDE, small-hop ending (no spin, no diagonals). Base: ALIGN state (push done, Mario held
LEFT into the wall corner at x 513.00). RIGHT r frames, then hold DOWN; after j frames of DOWN start a chain of n
small hops (A held h frames, re-hop on each landing), keep holding DOWN to the mirror. While Mario is above Laki
(y > ~20) Laki is capped at 6/frame. C-down tried on frames near the clip window. usage: pra18_ns_hops.py PART NPARTS OUT"""
import os, sys, json, math, itertools
MYARGS = list(sys.argv)
sys.argv = ['x', '0', '1', '/dev/null']
os.environ['JOBS'] = '[]'; os.environ['ALIGN'] = '1'
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_rta.py')).read().replace("print('done')", ''))
part, nparts, out = int(MYARGS[1]), int(MYARGS[2]), MYARGS[3]
def play(r, j, h, n, cd=None):
    e.load(base); log = []; f = 0
    for i in range(r):
        e.step(D_CBUTTON if cd == f else 0, *st(0, 80), 2); f += 1
    hops = 0; jt = None
    for i in range(80):
        q = player(e); grounded = q['action'] in (0, 1, 2); b = 0
        if i >= j and hops < n and grounded and (jt is None or jt > 3):
            jt = 0; hops += 1
        if jt is not None:
            if jt < h: b = A
            jt += 1
        if cd == f: b |= D_CBUTTON
        e.step(b, *st(90, 80), 2); q = player(e); f += 1
        log.append((f - 1, round(q['x'], 2), round(q['z'], 2), q['action'], round(L()[2], 2)))
        if cd is not None and f > cd + 30: break
    return log
jobs = list(itertools.product(range(0, 21), range(0, 13), (2, 3), (1, 2, 3, 4)))[part::nparts]
fo = open(out, 'a')
for job in jobs:
    log = play(*job)
    cands = [(f, x, z, a, sp) for f, x, z, a, sp in log if 560 <= x <= 578 and -22 <= z <= -12 and a in (0, 1, 2) and sp > 25]
    near = min(cands, key=lambda c: abs(c[4] - (616 - c[1])), default=None)
    hits = []
    for f, x, z, a, sp in cands:
        if 616 - x - 1.5 <= sp <= 616 - x + 0.6:
            play(*job, cd=f)
            if player(e)['action'] == 33 and player(e)['z'] > 0: hits.append((f, x, z, sp))
    rec = {'job': job, 'near': near, 'clips': hits}
    print(('CLIP ' if hits else '') + json.dumps(rec), flush=True)
    if hits: fo.write(json.dumps(rec) + '\n'); fo.flush()
print('done')
