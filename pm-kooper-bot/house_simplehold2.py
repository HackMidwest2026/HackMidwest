"""Blue House low entry, long approaches (mac_02, Speedy Spin equipped): positions chosen so that holding
up-left (45 deg) or left from far away passes Mario through the step-up strip at the corner (about x -395.6,
z -146..-140). up-left: x0 = c + z0 for c in [-258, -238] (0.02), z0 in {-134, -128, -120, -112}; left: z0 in
[-147, -136] (0.02), x0 in {-388, -380, -370, -360}. Each plain and with a spin on the first frame."""
import json, os, sys, multiprocessing as mp, collections, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
import house_stepgrid as S
import house_simplehold as SH
from pm import *


def run(job):
    name, x0, z0 = job
    e = H.W['e']
    if not S.place(e, x0, z0):
        return []
    e.step(0, 0, 0, 2)
    sp = os.path.join(H.W['d'], 'sh2.st'); e.save(sp)
    sx, sy = SH.INPUTS[name]
    out = []
    for spin in (0, 1):
        e.load(sp)
        maxy = 0
        for f in range(70):
            e.step(0x20 if (spin and f == 0) else 0, sx, sy, 2)
            p = player(e)
            maxy = max(maxy, p['y'])
            if H.inside(p):
                if maxy < 95:
                    out.append((name, x0, z0, spin, f, round(p['y'], 1)))
                break
            if p['x'] < -420 or p['z'] < -200:
                break
    return out


if __name__ == '__main__':
    jobs = []
    for z0 in (-134.0, -128.0, -120.0, -112.0):
        for i in range(0, 1001):
            c = -258.0 + 0.02 * i
            jobs.append(('up-left', round(c + z0, 2), z0))
    for x0 in (-388.0, -380.0, -370.0, -360.0):
        for i in range(0, 551):
            jobs.append(('left', x0, round(-147.0 + 0.02 * i, 2)))
    print(len(jobs), 'positions', flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=SH.init)
    t0, res = time.time(), []
    for i, out in enumerate(pool.imap_unordered(run, jobs, chunksize=16)):
        res += out
        for o in out: print('HIT', o, flush=True)
        if (i + 1) % 1000 == 0: print('%d/%d, %d hits [%.0fs]' % (i + 1, len(jobs), len(res), time.time() - t0), flush=True)
    json.dump(res, open(sys.argv[1], 'w'))
    print('done: %d hits' % len(res))
    print(sorted(collections.Counter((r[0], r[3]) for r in res).items()))
    pool.terminate()
