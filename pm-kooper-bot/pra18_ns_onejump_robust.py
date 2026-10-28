"""Robustness / cardinal variants of the one-jump no-spin hits (pra18_ns_onejump.py). usage: pra18_ns_onejump_robust.py"""
import os, sys
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_onejump.py')).read()
src = src[:src.index("INCH = [")]
sys.argv = ['x', '0', '1', '/dev/null']; exec(src)
def play2(inch, a1, k, h, a2, a3, cd=None):
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
        e.step(b, *(st(a, 80) if a is not None else (0, 0)), 2); q = player(e); f += 1
        log.append((f - 1, round(q['x'], 2), round(q['z'], 2), q['action'], round(L()[2], 2)))
        if cd is not None and f > cd + 30: break
    return log
def clips(job):
    out = []
    for c in play2(*job):
        if 550 <= c[1] <= 578 and c[2] > -24 and c[3] in (0, 1, 2) and c[4] > 25:
            play2(*job, cd=c[0])
            if player(e)['action'] == 33 and player(e)['z'] > 0: out.append(c)
    return out
REF = ((2, 7), 90, 6, 6, 90, 45)
print('REF', REF, clips(REF), flush=True)
for a3 in (90, None, 0, 180):
    j = list(REF); j[5] = a3; print('after landing stick', a3, clips(tuple(j)), flush=True)
for i, name, vals in ((2, 'walk-down frames k', (4, 5, 7, 8)), (3, 'A held', (2, 3, 4, 5, 8, 12))):
    for v in vals:
        j = list(REF); j[i] = v; print(name, v, clips(tuple(j)), flush=True)
for inch in ((1, 7), (3, 7), (2, 6), (2, 8), (0, 7), (4, 7)):
    j = list(REF); j[0] = inch; print('inch', inch, clips(tuple(j)), flush=True)
