"""from the wall-face landing (y 39), press A for h frames while holding stick (deg1, mag1) for the first k frames,
then hold up-slightly-right (276, full) for the rest. k = 90 means one direction the whole time."""
import json, multiprocessing as mp, os, sys, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_wallface as W
H = W.H
from corner_sweep import stick_for


def run(job):
    from pm import player, GAME_MODE, GM_WORLD
    deg, mag, h, k = job
    e = H.W['e']
    e.load(H.W['wf'])
    for f in range(90):
        st = stick_for(deg, mag) if f < k else stick_for(276, 80)
        e.step(0x80 if f < h else 0, st[0], st[1], 2)
        if e.s16(GAME_MODE) != GM_WORLD:
            break
        if H.inside(player(e)):
            return job + (f,)
    return None


if __name__ == '__main__':
    jobs = [(d, m, h, k) for d in range(0, 360, 2) for m in (80, 40, 20) for h in (1, 3, 6, 12) for k in (90, 6, 12)]
    pool = mp.get_context('spawn').Pool(4, initializer=W.init)
    t0 = time.time()
    res = [r for r in pool.map(run, jobs, chunksize=32) if r]
    json.dump(res, open(sys.argv[1], 'w'))
    print('%d of %d [%.0fs]' % (len(res), len(jobs), time.time() - t0))
    import collections
    for k in (90, 6, 12):
        for h in (1, 3, 6, 12):
            for m in (80, 40, 20):
                ds = sorted(r[0] for r in res if r[3] == k and r[2] == h and r[1] == m)
                if ds: print('k', k, 'A', h, 'mag', m, ':', ds)
    pool.terminate()
