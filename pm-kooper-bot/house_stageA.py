"""stage A: simple full jumps that land on the blue house's leaning wall face (collider 45, y > 25).
Start spots on a grid around the front-right corner (outside), A held 12 frames (or 4), one stick direction."""
import json, multiprocessing as mp, os, sys, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from house_probe3 import legal
from corner_sweep import stick_for


def run(job):
    from pm import player, GAME_MODE, GM_WORLD, COLLISION
    x0, z0 = job
    e = H.W['e']
    path = H.base(x0, z0)
    e.load(path)
    p = player(e)
    if abs(p['x'] - x0) > 0.3 or abs(p['z'] - z0) > 0.3:
        return []
    out = []
    for h in (12, 4):
        for mag in (80, 40, 20):
            for deg in range(0, 360, 3):
                e.load(path)
                st = stick_for(deg, mag)
                air = False
                for f in range(40):
                    e.step(0x80 if f < h else 0, st[0], st[1], 2)
                    q = player(e)
                    if q['action'] in (3, 4, 5, 8):
                        air = True
                    elif air:
                        if e.s16(COLLISION + 2) == 45 and q['y'] > 25:
                            out.append({'start': (x0, z0), 'deg': deg, 'mag': mag, 'h': h, 'f': f,
                                        'pos': (q['x'], q['y'], q['z'])})
                        break
    return out


if __name__ == '__main__':
    jobs = [(x, z) for x in range(-400, -339, 3) for z in range(-180, -114, 3)
            if legal(x, z) and not (x < -397 and z < -147)]
    print(len(jobs), 'spots', flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    t0, res = time.time(), []
    for i, r in enumerate(pool.imap_unordered(run, jobs)):
        res += r
        if (i + 1) % 50 == 0:
            print('%d/%d spots, %d wall-face landings [%.0fs]' % (i + 1, len(jobs), len(res), time.time() - t0), flush=True)
    json.dump(res, open(sys.argv[1], 'w'))
    print('done: %d wall-face landings [%.0fs]' % (len(res), time.time() - t0), flush=True)
    pool.terminate()
