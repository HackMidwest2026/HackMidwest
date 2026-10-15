"""from the hover loop at the blue house corner (wall-face jump (0,305,20,6,270), frame 7): hold stick a1 for n1
frames, then a2 for 30 frames. Looks for Mario inside the house."""
import json, multiprocessing as mp, os, sys, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_wallface as W
H = W.H
from corner_sweep import stick_for
JUMP = (0, 305, 20, 6, 270)
HOVER_F = 7


def init():
    W.init()
    e = H.W['e']
    e.load(H.W['wf'])
    d, deg, mag, hold, deg2 = JUMP
    s1 = stick_for(deg, mag); s2 = stick_for(deg2, 80)
    for f in range(HOVER_F + 1):
        e.step(0x80 if f < hold else 0, *(s1 if f < 6 else s2), 2)
    H.W['hv'] = os.path.join(H.W['d'], 'hover.st')
    e.save(H.W['hv'])


def run(job):
    from pm import player, GAME_MODE, GM_WORLD
    a1, m1, n1, a2, m2, b = job
    e = H.W['e']
    e.load(H.W['hv'])
    maxy, traj = 0, []
    for f in range(n1 + 30):
        st = stick_for(a1, m1) if f < n1 else stick_for(a2, m2)
        btn = 0x80 if (b and f == n1) else 0
        e.step(btn, st[0], st[1], 2)
        if e.s16(GAME_MODE) != GM_WORLD:
            break
        p = player(e)
        maxy = max(maxy, p['y'])
        traj.append((round(p['x'], 2), round(p['y'], 2), round(p['z'], 2), p['action']))
        if H.inside(p):
            return {'job': job, 'inside': traj[-1], 'f': f, 'maxy': maxy, 'traj': traj}
    return {'job': job, 'inside': None, 'maxy': maxy}


def main():
    jobs = [(a1, m1, n1, a2, m2, b) for a1 in range(0, 360, 15) for m1 in (80, 30, 10) for n1 in (1, 3, 6, 10)
            for a2 in range(0, 360, 15) for m2 in (80, 30) for b in (0,)]
    print(len(jobs), 'jobs', flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    t0, hits, maxy = time.time(), [], 0
    for r in pool.imap_unordered(run, jobs, chunksize=16):
        maxy = max(maxy, r['maxy'])
        if r['inside']:
            hits.append(r)
            if len(hits) <= 5:
                print('INSIDE', json.dumps({k: r[k] for k in ('job', 'inside', 'f', 'maxy')}), flush=True)
    json.dump(hits, open(sys.argv[1], 'w'))
    print('done %d jobs, %d inside, max y %.1f [%.0fs]' % (len(jobs), len(hits), maxy, time.time() - t0), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
