"""STEP_UP entry search at the blue house corner (mac_02).

Mario is placed at every point of a 0.1 x 0.25 grid in front of the corner (only placements that stay put after a
neutral frame, i.e. spots he can really stand on), then one frame of stick (direction, strength), then the same stick
for 12 more frames. Records step-ups (start position, facing) and any entry with max y < 95."""
import json, os, sys, multiprocessing as mp, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from corner_sweep import stick_for
from pm import *


def init():
    H.init()
    e = H.W['e']
    e.load(H.base(-380.0, -130.0))
    e.step(0, 0, 0, 2)
    H.W['ref'] = os.path.join(H.W['d'], 'ref.st'); e.save(H.W['ref'])


def place(e, x, z):
    e.load(H.W['ref'])
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 20.0); e.wf32(PLAYER + PS_POS + 8, z)
    e.step(0, 0, 0, 2)
    p = player(e)
    return abs(p['x'] - x) < 0.01 and abs(p['z'] - z) < 0.01 and p['action'] == 0


def run(x):
    e = H.W['e']
    out = {'x': x, 'stable': [], 'stepups': [], 'hits': []}
    for j in range(0, 29):
        z = round(-147.0 + 0.25 * j, 2)
        if not place(e, x, z):
            continue
        out['stable'].append(z)
        sp = os.path.join(H.W['d'], 'sg.st'); e.step(0, 0, 0, 2); e.save(sp)
        for mag in (80, 30):
            for deg in range(0, 360, 3):
                e.load(sp)
                st = stick_for(deg, mag)
                maxy, su = 0, None
                for f in range(13):
                    e.step(0, st[0], st[1], 2)
                    p = player(e)
                    maxy = max(maxy, p['y'])
                    if p['action'] == 34 and su is None:
                        su = (f, round(p['x'], 2), round(p['z'], 2), round(e.f32(PLAYER + 0x80)))
                        out['stepups'].append((z, mag, deg) + su)
                    if H.inside(p) and maxy < 95:
                        out['hits'].append((z, mag, deg, f, round(p['x'], 2), round(p['y'], 2), round(p['z'], 2)))
                        break
    return out


if __name__ == '__main__':
    xs = [round(-396.0 + 0.1 * i, 2) for i in range(0, 41)]
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    t0, res = time.time(), []
    for r in pool.imap_unordered(run, xs):
        res.append(r)
        print('x %.1f: %d stable spots, %d step-ups, %d low entries%s [%.0fs]' % (
            r['x'], len(r['stable']), len(r['stepups']), len(r['hits']), (' ' + str(r['hits'][:2])) if r['hits'] else '', time.time() - t0), flush=True)
        json.dump(res, open(sys.argv[1], 'w'))
    print('done', flush=True)
    pool.terminate()
