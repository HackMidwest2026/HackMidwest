"""from the corner-hug spot of the blue house (Mario standing at (-394.78, 20, -146.99), reached in the earlier
sweeps by walking lightly into the corner), try two-part inputs:
  part 1: stick (deg1, mag1) for n1 frames with none / A tap / Z on its first frame
  part 2: stick (deg2, mag2) for 25 frames with none / A held 12
Goal: inside the house while max y stays < 95."""
import json, os, sys, multiprocessing as mp, time, itertools
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from corner_sweep import stick_for
from pm import *
A_, Z_ = 0x80, 0x20
HUG = (-394.78, -146.99)


def run(job):
    deg1, mag1, n1, b1 = job
    e = H.W['e']
    base = H.base(*HUG)
    hits = []
    s1 = stick_for(deg1, mag1)
    for deg2 in range(0, 360, 15):
        for mag2 in (80, 30):
            for b2 in (0, 1):
                e.load(base)
                s2 = stick_for(deg2, mag2)
                maxy = 0
                for f in range(n1 + 25):
                    if f < n1:
                        b = {'tap': A_, 'spin': Z_}.get(b1, 0) if f == 0 else 0
                        st = s1
                    else:
                        g = f - n1
                        b = A_ if (b2 and g < 12) else 0
                        st = s2
                    e.step(b, st[0], st[1], 2)
                    p = player(e)
                    maxy = max(maxy, p['y'])
                    if maxy > 95:
                        break
                    if H.inside(p):
                        hits.append((deg2, mag2, b2, f, round(p['x'], 2), round(p['y'], 2), round(p['z'], 2), round(maxy, 1)))
                        break
    return job, hits


if __name__ == '__main__':
    jobs = list(itertools.product(range(0, 360, 10), (15, 40, 80), (1, 2, 3), ('none', 'tap', 'spin')))
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    t0, allh = time.time(), []
    for i, (job, hits) in enumerate(pool.imap_unordered(run, jobs, chunksize=4)):
        if hits:
            allh.append((job, hits))
            print('LOW ENTRY', job, hits[:3], len(hits), flush=True)
        if (i + 1) % 100 == 0:
            print('%d/%d [%.0fs]' % (i + 1, len(jobs), time.time() - t0), flush=True)
    json.dump(allh, open(sys.argv[1], 'w'))
    print('done: %d first parts lead to a low entry' % len(allh), flush=True)
    pool.terminate()
