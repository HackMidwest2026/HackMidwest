"""from each distinct wall-face landing (house_setup_tol), try every simple input for 40 frames: stick angle (5 deg),
strength, and none / A tap / A hold / Z spin on the first frame. Goal: inside the house with max y < 95."""
import json, os, sys, multiprocessing as mp, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H, house_setup_tol as T
from corner_sweep import stick_for
from pm import *
A_, Z_ = 0x80, 0x20


def prep(job):
    x0, a, k, amag, ang, rel = job
    e = H.W['e']
    e.load(T.stand_at_front(x0))
    sa = stick_for(a, 80)
    for f in range(k):
        e.step(Z_ if f == 0 else 0, sa[0], sa[1], 2)
    sl = stick_for(ang, amag)
    air = False
    for f in range(45):
        st = sl if f < rel else (0, 0)
        e.step(A_ if f < 12 else 0, st[0], st[1], 2)
        q = player(e)
        if q['action'] in (3, 4, 5, 8, 13):
            air = True
        elif air:
            break
    lp = os.path.join(H.W['d'], 'low_land.st'); e.save(lp)
    return lp, q


def run(r):
    e = H.W['e']
    lp, q0 = prep(tuple(r['job']))
    hits, best = [], (9e9, None)
    for kind in ('none', 'tap', 'hold', 'spin'):
        for mag in (80, 40, 15):
            for deg in range(0, 360, 5):
                e.load(lp)
                sx, sy = stick_for(deg, mag)
                maxy = 0
                for f in range(40):
                    b = {'tap': A_ if f == 0 else 0, 'hold': A_ if f < 12 else 0, 'spin': Z_ if f == 0 else 0}.get(kind, 0)
                    e.step(b, sx, sy, 2)
                    p = player(e)
                    maxy = max(maxy, p['y'])
                    if maxy > 95:
                        break
                    if p['x'] < -394 and p['z'] < best[0]:
                        best = (p['z'], (kind, mag, deg, f, round(p['x'], 2), round(p['y'], 2), round(p['z'], 2)))
                    if H.inside(p):
                        hits.append((kind, mag, deg, f, p['x'], p['y'], p['z'], maxy))
                        break
    return {'job': r['job'], 'land': r['land'], 'hits': hits, 'closest': best}


if __name__ == '__main__':
    L = json.load(open(sys.argv[2] if len(sys.argv) > 2 else 'house_landings.json'))
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    t0, res = time.time(), []
    for i, r in enumerate(pool.imap_unordered(run, L)):
        res.append(r)
        if r['hits']:
            print('LOW ENTRY', json.dumps({'job': r['job'], 'land': r['land'], 'hits': r['hits'][:4]}), len(r['hits']), flush=True)
        print('%d/%d landings, closest z with x < -394: %s [%.0fs]' % (i + 1, len(L), r['closest'], time.time() - t0), flush=True)
    json.dump(res, open(sys.argv[1], 'w'))
    print('done: %d landings with a low entry' % sum(1 for r in res if r['hits']), flush=True)
    pool.terminate()
