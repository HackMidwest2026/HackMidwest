"""pra_18 north->south RIGHT SIDE, 'pin + in-place jump' ending (aimed at RTA tolerance).
Base: ALIGN state (push done, Mario held LEFT into the wall corner at x 513.00). Then: inch DOWN d / RIGHT r frames
(Laki keeps hovering), Z spin holding s, keep holding DOWN-RIGHT (pins Mario in the mirror/pillar corner, x ~572),
jump in place at frame j after Z (A held h), optional 2nd jump on landing, then stand holding DOWN-RIGHT.
C-down tried where Laki's speed is near the clip window. usage: pra18_ns_pin.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
MYARGS = list(sys.argv)
sys.argv = ['x', '0', '1', '/dev/null']
os.environ['JOBS'] = '[]'; os.environ['ALIGN'] = '1'
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_rta.py')).read().replace("print('done')", ''))
part, nparts, out = int(MYARGS[1]), int(MYARGS[2]), MYARGS[3]
WIN = {}
for fn in ('/tmp/claude-0/pm/p18/win2.json', '/tmp/claude-0/pm/p18/win3.json', '/tmp/claude-0/pm/p18/win_569.json', '/tmp/claude-0/pm/p18/win_571.json', '/tmp/claude-0/pm/p18/win_573.json'):
    try:
        for k, v in json.load(open(fn)).items():
            x = float(k.split(',')[0])
            if v: WIN[x] = (min(v), max(v))
    except Exception: pass
def window(x):
    ks = sorted(WIN); best = min(ks, key=lambda k: abs(k - x))
    lo, hi = WIN[best]; sh = best - x                       # window slides ~1 speed per unit x
    return lo + sh, hi + sh
def play(d, r, s, j, h, n, cd=None):
    e.load(base); f = 0; log = []
    pre = [(0, 90)] * d + [(0, 0)] * r + [(0, None)] * 2
    for b, a in pre:
        if cd == f: b |= D_CBUTTON
        e.step(b, *(st(a, 80) if a is not None else (0, 0)), 2); f += 1
    jumps = 0; jt = None
    for i in range(80):
        q = player(e); b = Z if i == 0 else 0; a = s if i < 2 else 45
        grounded = q['action'] in (0, 1, 2, 26)
        if (i == j) or (jumps and jumps < n and jt is not None and jt > 3 and q['action'] in (0, 1, 2)):
            jt = 0; jumps += 1
        if jt is not None:
            if jt < h: b |= A
            jt += 1
        if cd == f: b |= D_CBUTTON
        e.step(b, *st(a, 80), 2); q = player(e); f += 1
        log.append((f - 1, round(q['x'], 2), round(q['z'], 2), q['action'], round(L()[2], 2)))
        if cd is not None and f > cd + 30: break
    return log
jobs = list(itertools.product(range(0, 8), range(0, 9), (45, 90), range(4, 34, 2), (3, 6), (1, 2)))[part::nparts]
fo = open(out, 'a')
for job in jobs:
    log = play(*job)
    cands = [(f, x, z, a, sp) for f, x, z, a, sp in log if 556 <= x <= 578 and -22 <= z <= -12 and a in (0, 1, 2) and sp > 25]
    def gap(c):
        lo, hi = window(c[1]); return 0 if lo <= c[4] <= hi else min(abs(c[4] - lo), abs(c[4] - hi))
    near = min(cands, key=gap, default=None)
    hits = []
    for c in cands:
        if gap(c) < 0.6:
            play(*job, cd=c[0])
            if player(e)['action'] == 33 and player(e)['z'] > 0: hits.append(c)
    rec = {'job': job, 'near': near, 'gap': round(gap(near), 2) if near else None, 'clips': hits}
    print(('CLIP ' if hits else '') + json.dumps(rec), flush=True)
    if hits: fo.write(json.dumps(rec) + '\n'); fo.flush()
print('done')
