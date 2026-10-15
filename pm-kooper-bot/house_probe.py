"""brute-force jumps and spin-jumps at the blue house's front-right corner (mac_02).

flags: standing on the house wall (collider 45) as a floor, and getting inside (x < -397, z < -147, inside the house box)."""
import json, math, multiprocessing as mp, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from corner_sweep import stick_for
A, Z = 0x0080, 0x0020
ROM = os.environ.get('PM_ROM', os.path.join(HERE, 'pm-jp.z64'))
W = {}


def init():
    from emu import Emu
    d = '/dev/shm/pmbot/hp%d' % os.getpid()
    os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(ROM, d), d


def base(x0, z0):
    from pm import PLAYER, PS_POS
    e = W['e']
    p = os.path.join(W['d'], 's_%.1f_%.1f.st' % (x0, z0))
    if not os.path.exists(p):
        e.load(os.path.join(HERE, 'states/mac02_start.st'))
        e.step(0, 0, 0, 2)
        e.wf32(PLAYER + PS_POS, x0); e.wf32(PLAYER + PS_POS + 4, 20.0); e.wf32(PLAYER + PS_POS + 8, z0)
        for i in range(6): e.step(0, 0, 0, 2)
        e.save(p)
    return p


def inside(p):
    return -547 < p['x'] < -397 and -342 < p['z'] < -147


def run(job):
    from pm import player, COLLISION, GAME_MODE, GM_WORLD
    x0, z0, mode, deg, k = job
    e = W['e']
    e.load(base(x0, z0))
    p = player(e)
    if abs(p['x'] - x0) > 0.5 or abs(p['z'] - z0) > 0.5 or inside(p):
        return None
    sx, sy = stick_for(deg, 80)
    out = {'job': job, 'wallfloor': [], 'inside': None, 'maxy': 0}
    for f in range(45):
        if mode == 'jump':
            b = A if f < k else 0
        else:  # spin, jump on spin frame k, hold A 12 frames
            b = Z if f == 0 else (A if k <= f < k + 12 else 0)
        e.step(b, sx, sy, 2)
        if e.s16(GAME_MODE) != GM_WORLD:
            break
        p = player(e)
        out['maxy'] = max(out['maxy'], p['y'])
        fl = e.s16(COLLISION + 2)
        if fl == 45 and p['action'] not in (3, 4, 5, 8):
            out['wallfloor'].append((f, round(p['x'], 2), round(p['y'], 2), round(p['z'], 2), p['action']))
        if inside(p):
            out['inside'] = (f, p['x'], p['y'], p['z'], p['action'])
            break
    return out


def main():
    jobs = []
    for x0 in [-384, -381, -378, -374, -370, -365]:
        for z0 in [-200, -175, -160, -150, -145, -140, -136, -132, -126, -118]:
            for deg in range(90, 271, 6):
                for k in (12, 6, 3):
                    jobs.append((x0, z0, 'jump', deg, k))
                for k in (1, 3, 6):
                    jobs.append((x0, z0, 'spin', deg, k))
    print(len(jobs), 'jobs', flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    res, t0 = [], time.time()
    for i, r in enumerate(pool.imap_unordered(run, jobs, chunksize=8)):
        if r is None:
            continue
        res.append(r)
        if r['inside'] or r['wallfloor']:
            print('HIT', json.dumps(r), flush=True)
    json.dump(res, open(sys.argv[1], 'w'))
    print('done %d runs [%.0fs]' % (len(res), time.time() - t0), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
