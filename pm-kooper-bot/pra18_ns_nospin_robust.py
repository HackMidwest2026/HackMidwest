"""Robustness of the no-spin RTA endings (pra18_ns_nospin2.py hits). job = (right r, down dn, jump1 stick, frames g of
running DOWN before jump 2, jump2 stick, A frames held on jump 2). Prints clipping C-down frames per variation and
where they fall relative to the final landing. usage: pra18_ns_nospin_robust.py"""
import os, sys
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_nospin2.py')).read()
src = src[:src.index("jobs = list(")]
sys.argv = ['x', '0', '1', '/dev/null']
exec(src)
def clips(job):
    log = play(*job)
    lands = [f for i, (f, x, z, a, sp) in enumerate(log) if a in (0, 1, 2) and i > 0 and log[i - 1][3] not in (0, 1, 2)]
    out = []
    for f, x, z, a, sp in log:
        if 560 <= x <= 580 and z > -24 and a in (0, 1, 2) and sp > 25:
            play(*job, cd=f)
            if player(e)['action'] == 33 and player(e)['z'] > 0: out.append((f, x, sp))
    return out, lands[-1] if lands else None
for REF in ((12, 4, 90, 1, 90, 5), (12, 6, 90, 0, 90, 5)):
    print('== REF', REF, clips(REF), flush=True)
    for i, name, vals in ((0, 'right', (10, 11, 13, 14)), (1, 'down', (REF[1] - 2, REF[1] - 1, REF[1] + 1, REF[1] + 2)),
                          (3, 'run between jumps', (0, 1, 2, 3)), (5, 'A held jump2', (3, 4, 6, 8, 12))):
        for v in vals:
            j = list(REF); j[i] = v
            if tuple(j) == REF: continue
            print(name, v, clips(tuple(j)), flush=True)
