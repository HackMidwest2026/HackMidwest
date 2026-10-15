"""tolerance of a human-style Blue House Skip setup (mac_02).

1. Mario stands pressed against the house front (walk up into it: z = -134) at x0.
2. Spin (Z) holding up-right (world angle a), jump (A, 12 frames) on spin frame k, hold down-left (ang) in the air.
3. If he lands on the leaning wall face: second jump, stick (deg2, mag2) for 6 frames, then up-slightly-right (276).
The air stick is released (neutral) after REL frames, before the landing.
Counts full successes over x0, a, k and air-stick strength."""
import json, os, sys, multiprocessing as mp, collections, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from corner_sweep import stick_for
from pm import *
A_, Z_ = 0x80, 0x20
SECOND = [(307, 15), (305, 15), (309, 15), (303, 30), (304, 30)]


def stand_at_front(x0):
    """Mario walked up into the house front at x0 (base state poked to z -130, then walk up 10 frames)"""
    e = H.W['e']
    p = os.path.join(H.W['d'], 'front_%.1f.st' % x0)
    if not os.path.exists(p):
        e.load(H.base(x0, -128.0))
        for f in range(10):
            e.step(0, *stick_for(270, 40), 2)
        for f in range(4):
            e.step(0, 0, 0, 2)
        e.save(p)
    return p


def run(job):
    x0, a, k, amag, ang, REL = job
    e = H.W['e']
    sp = stand_at_front(x0)
    e.load(sp)
    p0 = player(e)
    sa = stick_for(a, 80)
    for f in range(k):
        e.step(Z_ if f == 0 else 0, sa[0], sa[1], 2)
    sl = stick_for(ang, amag)
    air, landed = False, None
    for f in range(45):
        st = sl if f < REL else (0, 0)
        e.step(A_ if f < 12 else 0, st[0], st[1], 2)
        q = player(e)
        if q['action'] in (3, 4, 5, 8, 13):
            air = True
        elif air:
            if e.s16(COLLISION + 2) == 45 and q['y'] > 25:
                landed = q
            break
    if not landed:
        return {'job': job, 'start': (p0['x'], p0['z']), 'land': None, 'ok': []}
    lp = os.path.join(H.W['d'], 'tl.st'); e.save(lp)
    ok = []
    for deg2, mag2 in SECOND:
        e.load(lp)
        for f in range(80):
            st = stick_for(deg2, mag2) if f < 6 else stick_for(276, 80)
            e.step(A_ if f < 12 else 0, st[0], st[1], 2)
            if H.inside(player(e)):
                ok.append((deg2, mag2))
                break
    return {'job': job, 'start': (p0['x'], p0['z']), 'land': (landed['x'], landed['y'], landed['z']), 'ok': ok}


if __name__ == '__main__':
    jobs = [(x0, a, k, m, g, rel) for x0 in range(-426, -398, 2) for a in range(316, 345, 2) for k in range(6, 11) for m in (80, 40, 20) for g in range(140, 176, 5) for rel in (10, 12)]
    print(len(jobs), 'setups', flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    t0 = time.time()
    res = pool.map(run, jobs, chunksize=16)
    json.dump(res, open(sys.argv[1], 'w'))
    land = [r for r in res if r['land']]
    good = [r for r in res if r['ok']]
    print('%d setups: %d land on the wall face, %d get inside [%.0fs]' % (len(res), len(land), len(good), time.time() - t0))
    print('by spin frame k:', sorted(collections.Counter(r['job'][2] for r in good).items()))
    print('by start x:', sorted(collections.Counter(r['job'][0] for r in good).items()))
    print('by spin angle:', sorted(collections.Counter(r['job'][1] for r in good).items()))
    print('by air stick strength:', sorted(collections.Counter(r['job'][3] for r in good).items()))
    print('by air stick angle:', sorted(collections.Counter(r['job'][4] for r in good).items()))
    print('landing (by k):', sorted(collections.Counter(r['job'][2] for r in land).items()))
    pool.terminate()
