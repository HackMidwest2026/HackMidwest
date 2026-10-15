"""blue house (mac_02): approach the front-right corner, then switch the stick to angle a2 and hold it.
looks for STEP_UP (action 34) and for Mario ending inside the house."""
import json, math, multiprocessing as mp, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from corner_sweep import stick_for
import house_probe as H
CORNER = (-397.0, -147.0)


def run(job):
    from pm import player, COLLISION, GAME_MODE, GM_WORLD, PLAYER
    x0, z0, a1, n1, a2, mag = job
    e = H.W['e']
    e.load(H.base(x0, z0))
    p = player(e)
    if abs(p['x'] - x0) > 0.5 or abs(p['z'] - z0) > 0.5 or H.inside(p):
        return None
    out = {'job': job, 'stepup': [], 'inside': None}
    for f in range(n1 + 30):
        deg = a1 if f < n1 else a2
        sx, sy = stick_for(deg, mag)
        e.step(0, sx, sy, 2)
        if e.s16(GAME_MODE) != GM_WORLD:
            break
        p = player(e)
        if p['action'] == 34:
            out['stepup'].append((f, round(p['x'], 2), round(p['y'], 2), round(p['z'], 2), round(e.f32(PLAYER + 0x80), 1)))
        if H.inside(p):
            out['inside'] = (f, p['x'], p['y'], p['z'], p['action'])
            break
    return out


def main():
    jobs = []
    for r in (6, 10, 16, 24, 34):
        for a in range(-90, 181, 15):        # outside the house: east (x > -397) or front (z > -147)
            x0 = CORNER[0] + r * math.cos(math.radians(a))
            z0 = CORNER[1] + r * math.sin(math.radians(a))
            toward = (a + 180) % 360
            for off in (-30, -15, 0, 15, 30):
                for n1 in (2, 4, 6, 9, 13):
                    for a2 in range(0, 360, 10):
                        for mag in (80, 35):
                            jobs.append((round(x0, 2), round(z0, 2), (toward + off) % 360, n1, a2, mag))
    print(len(jobs), 'jobs', flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    res, t0, nsu, nin = [], time.time(), 0, 0
    for i, r in enumerate(pool.imap_unordered(run, jobs, chunksize=16)):
        if r is None:
            continue
        res.append(r)
        nsu += bool(r['stepup']); nin += bool(r['inside'])
        if r['inside']:
            print('INSIDE', json.dumps(r), flush=True)
        if (i + 1) % 5000 == 0:
            print('%d/%d  stepups %d  inside %d  [%.0fs]' % (i + 1, len(jobs), nsu, nin, time.time() - t0), flush=True)
    json.dump(res, open(sys.argv[1], 'w'))
    print('done %d runs, stepups %d, inside %d [%.0fs]' % (len(res), nsu, nin, time.time() - t0), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
