"""low Blue House entry with gentle sticks (mac_02): Mario standing at (x0, z0) near the working spot, hold raw stick
(sx, sy) for sy in 10..80 and sx from 0 to about 35% of sy to the left (walking to running), 60 frames.
x0 -395.30..-394.60 (0.01), z0 -146.9..-130.4 (0.5). Success = inside with max y < 95."""
import json, os, sys, multiprocessing as mp, collections, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
import house_stepgrid as S
from pm import *
STICKS = [(sx, sy) for sy in (10, 15, 20, 30, 40, 60, 80) for sx in range(-round(0.35 * sy), 1)]


def run(x0):
    e = H.W['e']
    out = []
    for j in range(0, 34):
        z0 = round(-146.9 + 0.5 * j, 2)
        if not S.place(e, x0, z0):
            continue
        e.step(0, 0, 0, 2)
        sp = os.path.join(H.W['d'], 'ww.st'); e.save(sp)
        for sx, sy in STICKS:
            e.load(sp)
            maxy = 0
            for f in range(60):
                e.step(0, sx, sy, 2)
                p = player(e)
                maxy = max(maxy, p['y'])
                if H.inside(p):
                    if maxy < 95:
                        out.append((x0, z0, sx, sy, f))
                    break
                if p['z'] >= -134.0 and f > 2 and abs(p['z'] + 134.0) < 0.01:
                    break          # stopped by the front wall
    return x0, out


if __name__ == '__main__':
    xs = [round(-395.30 + 0.01 * i, 2) for i in range(0, 71)]
    print(len(STICKS), 'sticks', flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=S.init)
    t0, res = time.time(), []
    for i, (x0, out) in enumerate(pool.imap_unordered(run, xs)):
        res += out
        print('x0 %.2f: %d hits [%.0fs]' % (x0, len(out), time.time() - t0), flush=True)
    json.dump(res, open(sys.argv[1], 'w'))
    print('done: %d hits' % len(res))
    print('by stick:', sorted(collections.Counter((r[2], r[3]) for r in res).items()))
    print('by x0:', sorted(collections.Counter(r[0] for r in res).items()))
    print('by z0:', sorted(collections.Counter(r[1] for r in res).items()))
    pool.terminate()
