"""at the best wall-face landing (spin_end 33, air stick (-36,-2)), list the second jumps that work, finely:
stick angle 0-359 (1 deg), strengths, held for k frames before switching to up-slightly-right (276)."""
import json, os, multiprocessing as mp, collections
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
import house_sens2 as S2
from corner_sweep import stick_for
from pm import *
A_ = 0x80


def init():
    H.init()
    r = S2.run((33, -36, -2, 12))
    H.W['lp'] = os.path.join(H.W['d'], 'best_land.st')
    os.rename(os.path.join(H.W['d'], 'land.st'), H.W['lp'])


def run(job):
    deg, mag, k, h = job
    e = H.W['e']
    e.load(H.W['lp'])
    for f in range(80):
        st = stick_for(deg, mag) if f < k else stick_for(276, 80)
        e.step(A_ if f < h else 0, st[0], st[1], 2)
        if e.s16(GAME_MODE) != GM_WORLD:
            return None
        if H.inside(player(e)):
            return job
    return None


if __name__ == '__main__':
    jobs = [(d, m, k, h) for d in range(0, 360) for m in (80, 50, 30, 15) for k in (0, 3, 6, 9) for h in (12, 6)]
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    ok = [r for r in pool.map(run, jobs, chunksize=64) if r]
    print(len(ok), 'of', len(jobs))
    by = collections.defaultdict(list)
    for d, m, k, h in ok:
        by[(m, k, h)].append(d)
    for key in sorted(by):
        print('mag %d, first %d frames, A %d:' % key, by[key])
    pool.terminate()
