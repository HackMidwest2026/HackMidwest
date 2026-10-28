"""Robustness of the pin + in-place-jump hits (pra18_ns_pin.py). usage: pra18_ns_pin_robust.py"""
import os, sys
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_pin.py')).read()
src = src[:src.index("jobs = list(")]
sys.argv = ['x', '0', '1', '/dev/null']; exec(src)
def clips(job):
    log = play(*job); out = []
    for f, x, z, a, sp in log:
        if 556 <= x <= 578 and z > -24 and a in (0, 1, 2) and sp > 25:
            play(*job, cd=f)
            if player(e)['action'] == 33 and player(e)['z'] > 0: out.append((f, x, sp))
    return out
for REF in ((1, 7, 90, 10, 3, 1), (4, 7, 90, 8, 6, 1)):
    print('== REF', REF, clips(REF), flush=True)
    for i, name, vals in ((0, 'inch down', range(0, 8)), (1, 'inch right', (5, 6, 8, 9)), (3, 'jump frame after Z', range(REF[3] - 4, REF[3] + 6)),
                          (4, 'A held', (2, 3, 4, 5, 6, 8)), (5, 'jumps', (2,))):
        for v in vals:
            j = list(REF); j[i] = v
            if tuple(j) != REF: print(name, v, clips(tuple(j)), flush=True)
