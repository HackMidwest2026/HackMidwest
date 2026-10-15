"""capture region at the blue house corner: place Mario at (x, y, z) (0.25-unit grid around the corner, heights
20..90), run one frame with no input, and record whether he ends inside the house box, outside, or on the line.
Shows where Mario's center has to be for the game's own push-out to put him inside."""
import json, os, sys, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from pm import *


def init():
    H.init()
    e = H.W['e']
    e.load(H.base(-380.0, -130.0))
    e.step(0, 0, 0, 2)
    H.W['ref'] = os.path.join(H.W['d'], 'ref.st'); e.save(H.W['ref'])


def run(y):
    e = H.W['e']
    out = []
    for i in range(0, 41):
        for j in range(0, 41):
            x, z = -400.0 + 0.25 * i, -150.0 + 0.25 * j
            e.load(H.W['ref'])
            e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, y); e.wf32(PLAYER + PS_POS + 8, z)
            e.step(0, 0, 0, 2)
            p = player(e)
            out.append((x, z, round(p['x'], 2), round(p['z'], 2), H.inside(p)))
    return y, out


if __name__ == '__main__':
    ys = [20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0]
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    res = dict(pool.map(run, ys))
    json.dump({str(k): v for k, v in res.items()}, open(sys.argv[1], 'w'))
    for y in ys:
        ins = [(x, z) for x, z, px, pz, i in res[y] if i]
        out_in = [(x, z) for x, z in ins if not (x < -397 and z < -147)]   # started outside the box, ended inside
        print('y %.0f: %d of %d placements end inside; %d of those started outside the box (x >= -397 or z >= -147): %s' % (
            y, len(ins), len(res[y]), len(out_in), out_in[:12]))
    pool.terminate()
