"""simplest blue house setups: Mario standing at (x, z) near the front-right corner, press A (hold h frames) and
hold one stick direction for 90 frames. Grid of start spots x 1-degree angles."""
import json, math, multiprocessing as mp, os, sys, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from house_probe3 import legal
from corner_sweep import stick_for


def run(job):
    from pm import player, GAME_MODE, GM_WORLD
    x0, z0, mags, holds = job
    e = H.W['e']
    path = H.base(x0, z0)
    e.load(path)
    p = player(e)
    if abs(p['x'] - x0) > 0.3 or abs(p['z'] - z0) > 0.3:
        return []
    out = []
    for mag in mags:
        for h in holds:
            for deg in range(180, 361, 2):
                e.load(path)
                st = stick_for(deg % 360, mag)
                for f in range(90):
                    e.step(0x80 if f < h else 0, st[0], st[1], 2)
                    if e.s16(GAME_MODE) != GM_WORLD:
                        break
                    q = player(e)
                    if H.inside(q):
                        out.append((x0, z0, deg % 360, mag, h, f))
                        break
    return out


if __name__ == '__main__':
    jobs = []
    for x in [-400 + 1.0 * i for i in range(0, 21)]:
        for z in [-150 + 1.0 * j for j in range(0, 21)]:
            if legal(x, z) and not (x < -397 and z < -147):
                jobs.append((x, z, (80, 40), (12, 4)))
    print(len(jobs), 'spots', flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    t0, hits = time.time(), []
    for r in pool.imap_unordered(run, jobs):
        hits += r
        for h in r[:2]:
            print('INSIDE', h, flush=True)
    json.dump(hits, open(sys.argv[1], 'w'))
    print('done: %d hits [%.0fs]' % (len(hits), time.time() - t0), flush=True)
    pool.terminate()
