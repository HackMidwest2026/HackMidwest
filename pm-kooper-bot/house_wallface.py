"""from the moment Mario lands on the blue house's leaning wall face (house_explore top.json, frame 46),
try every jump: delay d, stick angle, strength, A hold length, then a second stick angle in the air."""
import json, multiprocessing as mp, os, sys, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from house_explore import BASES
from corner_sweep import stick_for
A_, Z_ = 0x80, 0x20
V = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/house_wallface_approach.json')))
LAND_F = 46


def init():
    H.init()
    from pm import player
    e = H.W['e']
    e.load(H.base(*BASES[V['bi']]))
    f = 0
    for b, deg, mag, n in V['seq']:
        sx, sy = stick_for(deg, mag) if deg is not None else (0, 0)
        for i in range(n):
            if f > LAND_F:
                break
            bb = {'tap': A_ if i == 0 else 0, 'spin': Z_ if i == 0 else 0, 'hold': A_}.get(b, 0)
            e.step(bb, sx, sy, 2)
            f += 1
    H.W['wf'] = os.path.join(H.W['d'], 'wallface.st')
    e.save(H.W['wf'])
    H.W['p0'] = player(e)


def run(job):
    from pm import player, GAME_MODE, GM_WORLD
    d, deg, mag, hold, deg2 = job
    e = H.W['e']
    e.load(H.W['wf'])
    s1 = stick_for(deg, mag)
    s2 = stick_for(deg2, 80) if deg2 is not None else s1
    traj = []
    for f in range(d + 45):
        g = f - d
        b = A_ if 0 <= g < hold else 0
        st = s1 if g < 6 else s2
        e.step(b, st[0], st[1], 2)
        if e.s16(GAME_MODE) != GM_WORLD:
            break
        p = player(e)
        traj.append((round(p['x'], 2), round(p['y'], 2), round(p['z'], 2), p['action']))
        if H.inside(p):
            return {'job': job, 'inside': traj[-1], 'f': f, 'maxy': max(t[1] for t in traj)}
    return {'job': job, 'inside': None, 'maxy': max(t[1] for t in traj)}


def main():
    jobs = [(d, deg, mag, hold, deg2) for d in (0, 1) for deg in range(0, 360, 5) for mag in (80, 40, 20)
            for hold in (1, 3, 6, 12) for deg2 in (None, 180, 225, 270)]
    print(len(jobs), 'jobs', flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    t0, hits, maxy = time.time(), [], 0
    for i, r in enumerate(pool.imap_unordered(run, jobs, chunksize=16)):
        maxy = max(maxy, r['maxy'])
        if r['inside']:
            hits.append(r)
            if len(hits) <= 10:
                print('INSIDE', json.dumps(r), flush=True)
    json.dump(hits, open(sys.argv[1], 'w'))
    print('done %d jobs, %d inside, max y %.1f [%.0fs]' % (len(jobs), len(hits), maxy, time.time() - t0), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
