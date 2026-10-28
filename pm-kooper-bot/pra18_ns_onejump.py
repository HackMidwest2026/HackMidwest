"""pra_18 N->S right side, ONE jump, no spin. Base: ALIGN state (Mario in the wall corner at x 513.00, Laki hovering).
Inch (d down, r right) while Laki hovers, walk a1 for k frames, ONE jump (A held h) holding a2, after landing hold a3.
C-down tried on frames near the clip window. usage: pra18_ns_onejump.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
MYARGS = list(sys.argv)
sys.argv = ['x', '0', '1', '/dev/null']
os.environ['JOBS'] = '[]'; os.environ['ALIGN'] = '1'
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_rta.py')).read().replace("print('done')", ''))
part, nparts, out = int(MYARGS[1]), int(MYARGS[2]), MYARGS[3]
W = {569.0: (46.1, 47.0), 570.0: (45.3, 46.0), 571.0: (44.4, 45.0), 572.0: (43.5, 44.0), 573.0: (42.7, 43.0), 574.0: (41.8, 42.0), 575.0: (41.0, 41.0)}
for fn in ('/tmp/claude-0/pm/p18/win2.json', '/tmp/claude-0/pm/p18/win3.json'):
    for k_, v in json.load(open(fn)).items():
        if v: W[float(k_.split(',')[0])] = (min(v), max(v))
def gap(x, s):
    k_ = min(W, key=lambda q: abs(q - x)); lo, hi = W[k_]; sh = k_ - x
    lo, hi = lo + sh, hi + sh
    return 0 if lo <= s <= hi else min(abs(s - lo), abs(s - hi))
def play(inch, a1, k, h, a2, a3, cd=None):
    d, r = inch
    e.load(base); f = 0; log = []
    seq = [(0, 90)] * d + [(0, 0)] * r + [(0, None)] * 2 + [(0, a1)] * k
    for b, a in seq:
        if cd == f: b |= D_CBUTTON
        e.step(b, *(st(a, 80) if a is not None else (0, 0)), 2); f += 1
    jt = 0; landed = False
    for i in range(70):
        q = player(e)
        if jt > 3 and q['action'] in (0, 1, 2): landed = True
        b = A if jt < h else 0; jt += 1
        a = a3 if landed else a2
        if cd == f: b |= D_CBUTTON
        e.step(b, *st(a, 80), 2); q = player(e); f += 1
        log.append((f - 1, round(q['x'], 2), round(q['z'], 2), q['action'], round(L()[2], 2)))
        if cd is not None and f > cd + 30: break
    return log
INCH = [(0, 0), (3, 3), (5, 5), (7, 2), (2, 7), (6, 0), (0, 8)]
jobs = list(itertools.product(INCH, (0, 45, 90), range(0, 25), (2, 4, 6), (0, 45, 90), (90, 45)))[part::nparts]
fo = open(out, 'a')
for job in jobs:
    log = play(*job)
    cands = [c for c in log if 556 <= c[1] <= 578 and -22 <= c[2] <= -12 and c[3] in (0, 1, 2) and c[4] > 25]
    near = min(cands, key=lambda c: gap(c[1], c[4]), default=None)
    hits = []
    for c in cands:
        if gap(c[1], c[4]) < 0.6:
            play(*job, cd=c[0])
            if player(e)['action'] == 33 and player(e)['z'] > 0: hits.append(c)
    rec = {'job': job, 'near': near, 'gap': round(gap(near[1], near[4]), 2) if near else None, 'clips': hits}
    print(('CLIP ' if hits else '') + json.dumps(rec), flush=True)
    if hits: fo.write(json.dumps(rec) + '\n'); fo.flush()
print('done')
