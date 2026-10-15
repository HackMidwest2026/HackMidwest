"""human-style low Blue House entry: Mario standing at (x0, z0) in front of the house (against the front wall at
z -134, or a bit away from it), hold ONE raw stick (sx, sy) for 60 frames. Walls slide him into line, so this tests
whether a single held direction from a rough spot is enough. Success = inside with max y < 95."""
import json, os, sys, multiprocessing as mp, collections
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
import house_stepgrid as S
from pm import *


def run(job):
    x0, z0 = job
    e = H.W['e']
    e.load(H.W['ref'])
    e.wf32(PLAYER + PS_POS, x0); e.wf32(PLAYER + PS_POS + 4, 20.0); e.wf32(PLAYER + PS_POS + 8, z0)
    for i in range(4): e.step(0, 0, 0, 2)
    sp = os.path.join(H.W['d'], 'lh.st'); e.save(sp)
    p0 = player(e)
    out = []
    for sy in (80, 60):
        for sx in range(-40, 41):
            e.load(sp)
            maxy = 0
            for f in range(60):
                e.step(0, sx, sy, 2)
                p = player(e)
                maxy = max(maxy, p['y'])
                if H.inside(p):
                    if maxy < 95:
                        out.append((round(p0['x'], 2), round(p0['z'], 2), sx, sy, f))
                    break
    return out


if __name__ == '__main__':
    jobs = [(float(x), float(z)) for x in range(-410, -379) for z in (-134, -130, -124, -116)]
    pool = mp.get_context('spawn').Pool(4, initializer=S.init)
    res = [r for out in pool.map(run, jobs, chunksize=2) for r in out]
    json.dump(res, open(sys.argv[1], 'w'))
    print('done: %d successes' % len(res))
    for r in res[:40]: print(r)
    print('by stick:', sorted(collections.Counter((r[2], r[3]) for r in res).items()))
    print('by start:', sorted(collections.Counter((r[0], r[1]) for r in res).items()))
    pool.terminate()
