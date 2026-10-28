"""pra_18 N->S right side, no spin, cardinal only, TWO FULL jumps (A held 6 = same as holding longer).
Base: ALIGN state (Mario in the wall corner at x 513.00). Inch DOWN d (free, Laki hovers), RIGHT r, DOWN dn, jump 1
holding DOWN, re-jump g frames after landing holding s2, then hold DOWN. usage: pra18_ns_twofull.py PART NPARTS OUT"""
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
def play(d, r, dn, g, s2, cd=None):
    e.load(base); f = 0; log = []
    seq = [90] * d + [None] * 2 + [0] * r + [90] * dn
    for a in seq:
        e.step(D_CBUTTON if cd == f else 0, *(st(a, 80) if a is not None else (0, 0)), 2); f += 1
    phase = 1; jt = 0; wait = 0
    for i in range(80):
        q = player(e); gr = q['action'] in (0, 1, 2); b = 0; a = 90
        if phase == 1:
            b = A if jt < 6 else 0; jt += 1
            if jt > 3 and gr: phase = 2; wait = 0
        if phase == 2:
            if wait >= g: phase = 3; jt = 0
            else: wait += 1
        if phase == 3:
            b = A if jt < 6 else 0; jt += 1; a = s2
            if jt > 3 and gr: phase = 4
        if phase == 4: a = 90
        if cd == f: b |= D_CBUTTON
        e.step(b, *st(a, 80), 2); q = player(e); f += 1
        log.append((f - 1, round(q['x'], 2), round(q['z'], 2), q['action'], round(L()[2], 2)))
        if cd is not None and f > cd + 30: break
    return log
jobs = list(itertools.product((0, 3, 5, 7), range(0, 15), range(0, 13), (0, 1, 2, 3), (90, 0)))[part::nparts]
fo = open(out, 'a')
for job in jobs:
    log = play(*job)
    cands = [c for c in log if 550 <= c[1] <= 578 and -22 <= c[2] <= -12 and c[3] in (0, 1, 2) and c[4] > 25]
    near = min(cands, key=lambda c: gap(c[1], c[4]), default=None)
    hits = []
    for c in cands:
        if gap(c[1], c[4]) < 0.8:
            play(*job, cd=c[0])
            if player(e)['action'] == 33 and player(e)['z'] > 0: hits.append(c)
    rec = {'job': job, 'near': near, 'gap': round(gap(near[1], near[4]), 2) if near else None, 'clips': hits}
    print(('CLIP ' if hits else '') + json.dumps(rec), flush=True)
    if hits: fo.write(json.dumps(rec) + '\n'); fo.flush()
print('done')
