"""Blue House low entry with the simplest inputs (mac_02), Speedy Spin equipped.

Mario stands at (x0, z0) (every standable spot of a 0.02 x 0.5 grid around the working spot (-395.2, -141)), then holds
ONE full-tilt direction: up (0, 80), up-left (-57, 57) or left (-80, 0), either plain or with Z (spin) on the first
frame. Success = inside the house with max y < 95 within 45 frames."""
import json, os, sys, multiprocessing as mp, collections, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
import house_stepgrid as S
from pm import *
SPEEDY_SPIN = 0x11F
INPUTS = {'up': (0, 80), 'up-left': (-57, 57), 'left': (-80, 0)}


def init():
    S.init()
    e = H.W['e']
    e.load(H.W['ref'])
    e.w16(PLAYER_DATA + 0x208, SPEEDY_SPIN)       # equip Speedy Spin in the first badge slot
    e.step(0, 0, 0, 2)
    e.save(H.W['ref'])


def run(x0):
    e = H.W['e']
    out = []
    for j in range(0, 54):
        z0 = round(-146.9 + 0.5 * j, 2)
        if not S.place(e, x0, z0):
            continue
        e.step(0, 0, 0, 2)
        sp = os.path.join(H.W['d'], 'sh.st'); e.save(sp)
        for name, (sx, sy) in INPUTS.items():
            for spin in (0, 1):
                e.load(sp)
                maxy, su = 0, False
                for f in range(45):
                    e.step(0x20 if (spin and f == 0) else 0, sx, sy, 2)
                    p = player(e)
                    maxy = max(maxy, p['y'])
                    su = su or p['action'] == 34
                    if H.inside(p):
                        if maxy < 95:
                            out.append((x0, z0, name, spin, f, round(p['y'], 1), su))
                        break
                    if abs(p['x'] - x0) > 40 or p['z'] > z0 + 20:
                        break
    return x0, out


if __name__ == '__main__':
    xs = [round(-397.0 + 0.02 * i, 2) for i in range(0, 201)]
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    t0, res = time.time(), []
    for i, (x0, out) in enumerate(pool.imap_unordered(run, xs)):
        res += out
        if out: print('x0 %.2f:' % x0, out, flush=True)
        if (i + 1) % 20 == 0: print('%d/%d columns, %d successes [%.0fs]' % (i + 1, len(xs), len(res), time.time() - t0), flush=True)
    json.dump(res, open(sys.argv[1], 'w'))
    print('done: %d successes' % len(res))
    print('by input:', sorted(collections.Counter((r[2], r[3]) for r in res).items()))
    pool.terminate()
