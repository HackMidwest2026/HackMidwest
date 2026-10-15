"""low Blue House entry via STEP_UP (mac_02).

From the corner-hug spot (Mario standing at (-394.78, 20, -146.99)), walk left (world 180) at strength m; from frame s
on, hold world angle t (left-up .. up) for 20 frames. STEP_UP moves Mario 3 units per frame along the stick direction
of the frame it triggers on, with no movement wall test, so a step-up facing up-left from the hug line should carry
his center past both wall lines, and the push-out then puts him inside. Goal: inside with max y < 95."""
import json, os, sys, multiprocessing as mp, itertools, collections
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from corner_sweep import stick_for
from pm import *
HUG = (-394.78, -146.99)


def run(job):
    m, s, t, mt = job
    e = H.W['e']
    e.load(H.base(*HUG))
    maxy, su = 0, None
    for f in range(s + 20):
        st = stick_for(180, m) if f < s else stick_for(t, mt)
        e.step(0, st[0], st[1], 2)
        p = player(e)
        maxy = max(maxy, p['y'])
        if p['action'] == 34 and su is None:
            su = (f, round(p['x'], 2), round(p['y'], 2), round(p['z'], 2), round(e.f32(PLAYER + 0x80)))
        if H.inside(p):
            return job, (f, round(p['x'], 2), round(p['y'], 2), round(p['z'], 2), round(maxy, 1)), su
    return job, None, su


if __name__ == '__main__':
    jobs = list(itertools.product((10, 15, 20, 30, 45, 80), range(0, 7), range(180, 292, 2), (80, 40, 15)))
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    res = pool.map(run, jobs, chunksize=32)
    hits = [r for r in res if r[1] and r[1][4] < 95]
    json.dump(res, open(sys.argv[1], 'w'))
    print('%d of %d inputs get inside low; %d trigger a step-up' % (len(hits), len(res), sum(1 for r in res if r[2])))
    for r in hits[:15]: print(r)
    print('by walk strength:', sorted(collections.Counter(r[0][0] for r in hits).items()))
    print('by switch frame:', sorted(collections.Counter(r[0][1] for r in hits).items()))
    print('by angle:', sorted(collections.Counter(r[0][2] for r in hits).items()))
    pool.terminate()
