"""window of the low (step-up) Blue House entry: Mario standing at (x0, z0) in front of the corner, hold one raw stick
(sx, sy) until he is inside (40 frames max). x0 on a 0.02 grid, z0 every 1.0 from -146.5 to -125.5, sx -24..8 (step 2), sy 80."""
import json, os, sys, multiprocessing as mp, collections
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
import house_stepgrid as S
from pm import *


def run(x0):
    e = H.W['e']
    out = []
    for j in range(0, 22):
        z0 = round(-146.5 + 1.0 * j, 2)
        if not S.place(e, x0, z0):
            continue
        e.step(0, 0, 0, 2)
        sp = os.path.join(H.W['d'], 'lw.st')
        e.save(sp)
        for sy in (80,):
            for sx in range(-24, 9, 2):
                e.load(sp)
                maxy = 0
                for f in range(40):
                    e.step(0, sx, sy, 2)
                    p = player(e)
                    maxy = max(maxy, p['y'])
                    if H.inside(p):
                        if maxy < 95:
                            out.append((x0, z0, sx, sy, f, round(maxy, 1)))
                        break
                    if p['z'] > z0 + 5:
                        break
    return x0, out


if __name__ == '__main__':
    xs = [round(-396.0 + 0.02 * i, 2) for i in range(0, 151)]
    pool = mp.get_context('spawn').Pool(4, initializer=S.init)
    res = []
    for x0, out in pool.imap_unordered(run, xs):
        res += out
        print('x0 %.2f: %d' % (x0, len(out)), flush=True)
    json.dump(res, open(sys.argv[1], 'w'))
    print('done: %d successes' % len(res))
    print('x0:', sorted(collections.Counter(r[0] for r in res).items()))
    print('z0:', sorted(collections.Counter(r[1] for r in res).items()))
    print('sx (sy 80):', sorted(collections.Counter(r[2] for r in res if r[3] == 80).items()))
    print('sy:', sorted(collections.Counter(r[3] for r in res).items()))
    pool.terminate()
