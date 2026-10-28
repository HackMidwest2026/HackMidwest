"""pra_18 N->S right side, 'leave the tether in the air' ending. Base: ALIGN state (Mario in the wall corner at
x 513.00, Laki hovering). Inch DOWN d / RIGHT r frames (free), then a chain of n full jumps (A held 6): jump 1 holding
s1 starts while Mario is still within 40 of Laki (so Laki starts out capped at 6/frame and slides past the north-wall
bump instead of hopping), later jumps holding s2, each re-pressed g frames after landing; after the last landing hold
DOWN-RIGHT (pins Mario in the mirror/pillar corner) and stand. C-down tried on frames near the clip window.
usage: pra18_ns_airexit.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
MYARGS = list(sys.argv)
sys.argv = ['x', '0', '1', '/dev/null']
os.environ['JOBS'] = '[]'; os.environ['ALIGN'] = '1'
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_rta.py')).read().replace("print('done')", ''))
part, nparts, out = int(MYARGS[1]), int(MYARGS[2]), MYARGS[3]
def play(d, r, s1, s2, n, g, cd=None, N=110):
    e.load(base); f = 0; log = []
    for a, k in ((90, d), (0, r)):
        for i in range(k): e.step(0, *st(a, 80), 2); f += 1
    for i in range(2): e.step(0, 0, 0, 2); f += 1
    jumps = 0; jt = 0; wait = None; done_t = None
    for i in range(N):
        q = player(e); gr = q['action'] in (0, 1, 2)
        b = 0
        if jumps == 0: jumps = 1; jt = 0
        elif jumps < n and gr and jt > 3:
            wait = 0 if wait is None else wait + 1
            if wait >= g: jumps += 1; jt = 0; wait = None
        if jt < 6 and (jumps < n or not gr or jt < 6): b = A if jt < 6 else 0
        a = s1 if jumps == 1 else s2
        if jumps == n and gr and jt > 3: a = 45
        jt += 1
        if cd == f: b |= D_CBUTTON
        e.step(b, *st(a, 80), 2); q = player(e); f += 1
        log.append((f - 1, round(q['x'], 2), round(q['z'], 2), q['action'], round(L()[2], 2)))
        if cd is not None and f > cd + 30: break
    return log
if MYARGS[1] != 'lib':
    jobs = list(itertools.product(range(0, 8), range(0, 9), (0, 45, 90), (45, 90), (1, 2, 3), (0, 1, 2)))[part::nparts]
    fo = open(out, 'a')
    for job in jobs:
        log = play(*job)
        cands = [c for c in log if c[4] > 25 and 556 <= c[1] <= 578 and c[2] > -24 and c[3] in (0, 1, 2)]
        hits = []
        for c in cands[:5]:
            play(*job, cd=c[0])
            if player(e)['action'] == 33 and player(e)['z'] > 0: hits.append(c)
        rec = {'job': job, 'cands': cands[:3], 'clips': hits}
        print(('CLIP ' if hits else '') + json.dumps(rec), flush=True)
        if hits: fo.write(json.dumps(rec) + '\n'); fo.flush()
    print('done')
