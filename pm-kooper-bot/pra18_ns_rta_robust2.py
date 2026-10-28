"""Robustness of the ALIGNED RTA ending (hold LEFT along the north wall to x 513.00 first):
right n0 frames, Z holding DOWN-RIGHT, A k frames after Z (held h) holding DOWN, keep holding d3 after landing,
C-down. Reports the frames on which C-down clips for each variation. usage: pra18_ns_rta_robust2.py"""
import os, sys, json, math, itertools
sys.argv = ['x', '0', '1', '/dev/null']
os.environ['JOBS'] = '[]'; os.environ['ALIGN'] = '1'; os.environ.setdefault('D0', '0')
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pra18_ns_rta.py')).read().replace("print('done')", ''))
def cd_frames(job):
    log, landed = play(*job)
    out = []
    for f, x, z, a, sp in log:
        if 560 <= x <= 580 and z > -24 and sp > 25:
            play(*job, cd=f); r = player(e)
            if r['action'] == 33 and r['z'] > 0: out.append((f, x, round(sp, 2)))
    return out
REF = eval(os.environ.get('REF', '(1, 0, 45, 7, 6, 90, 8, 90)'))
print('REF', cd_frames(REF), flush=True)
for i, name, vals in ((1, 'wait before Z', (1, 5, 20)), (0, 'walk frames', (REF[0] - 2, REF[0] - 1, REF[0] + 1, REF[0] + 2)), (3, 'Z->A frames', (5, 6, 8, 9)),
                      (4, 'A held', (3, 4, 5, 8, 12)), (6, 'hold after landing', (0, 2, 4, 15, 30)), (7, 'stick after landing', (45, 0, 135))):
    for v in vals:
        j = list(REF); j[i] = v
        print(name, v, cd_frames(tuple(j)), flush=True)
