"""pra_18 north->south RIGHT SIDE, WALK-ONLY ending (no spin, no jump, no diagonals).
Base: pra18_ns_rta.py ALIGN state (push done, Mario held LEFT into the wall corner at x 513.00). Then:
DOWN d frames, RIGHT r frames, then hold DOWN to the mirror (and keep holding). C-down is tried on frames where
Laki's speed is near the clip window. usage: pra18_ns_walk.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
MYARGS = list(sys.argv)
sys.argv = ['x', '0', '1', '/dev/null']
os.environ['JOBS'] = '[]'; os.environ['ALIGN'] = '1'
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_rta.py')).read().replace("print('done')", ''))
part, nparts, out = int(MYARGS[1]), int(MYARGS[2]), MYARGS[3]
def play(d, r, cd=None, n=70):
    e.load(base); log = []
    plan = [90] * d + [0] * r + [90] * n
    for f, a in enumerate(plan):
        e.step(D_CBUTTON if cd == f else 0, *st(a, 80), 2); q = player(e)
        log.append((f, round(q['x'], 2), round(q['z'], 2), q['action'], round(L()[2], 2)))
        if cd is not None and f > cd + 30: break
    return log
jobs = list(itertools.product(range(0, 31), range(0, 41)))[part::nparts]
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
    rec = {'job': job, 'near': near, 'maxsp': max(r[4] for r in log), 'end': log[-1][1:3], 'clips': hits}
    print(('CLIP ' if hits else '') + json.dumps(rec), flush=True)
    if hits: fo.write(json.dumps(rec) + '\n'); fo.flush()
print('done')
