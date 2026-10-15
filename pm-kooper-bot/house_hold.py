"""from the blue house hover loop, hold ONE stick direction (every 1 degree, several strengths) for 60 frames,
starting at each of the 5 frames of the loop. Which single held inputs get Mario inside?"""
import json, multiprocessing as mp, os, sys, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_hover as HV
H = HV.H
from corner_sweep import stick_for


def run(job):
    from pm import player, GAME_MODE, GM_WORLD
    deg, mag, phase = job
    e = H.W['e']
    e.load(H.W['hv'])
    for f in range(phase):
        e.step(0, *stick_for(270, 80), 2)
    st = stick_for(deg, mag)
    for f in range(60):
        e.step(0, st[0], st[1], 2)
        p = player(e)
        if H.inside(p):
            return (deg, mag, phase, f, True)
    return (deg, mag, phase, None, False)


if __name__ == '__main__':
    jobs = [(d, m, ph) for d in range(0, 360) for m in (15, 30, 50, 80) for ph in range(5)]
    pool = mp.get_context('spawn').Pool(4, initializer=HV.init)
    t0 = time.time()
    res = pool.map(run, jobs, chunksize=32)
    ok = [r for r in res if r[4]]
    json.dump(res, open(sys.argv[1], 'w'))
    print('%d of %d single held inputs get inside [%.0fs]' % (len(ok), len(res), time.time() - t0))
    import collections
    for m in (15, 30, 50, 80):
        for ph in range(5):
            degs = sorted(r[0] for r in ok if r[1] == m and r[2] == ph)
            print('mag', m, 'phase', ph, ':', degs[:3], '...', degs[-3:], len(degs))
    pool.terminate()
