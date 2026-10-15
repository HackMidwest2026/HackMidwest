"""Mario placed on the ground at points in the blue house corner notch (half-unit grid), holding one stick direction
(world angles 180-290, i.e. left through up) at several strengths, optionally with a hop. Looks for STEP_UP and for
Mario ending inside the house while staying low (max y < 95)."""
import json, os, sys, multiprocessing as mp, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from corner_sweep import stick_for
from pm import *
A_ = 0x80


def run(pt):
    try:
        return run1(pt)
    except Exception as ex:
        return {'pt': pt, 'start': None, 'hits': [], 'stepups': 0, 'err': str(ex)}


def run1(pt):
    x0, z0 = pt
    e = H.W['e']
    sp = H.base(x0, z0)
    e.load(sp)
    p = player(e)
    if p['action'] != 0 or abs(p['y'] - 20) > 0.5:
        return {'pt': pt, 'start': None, 'hits': [], 'stepups': 0}
    start = (p['x'], p['z'])
    hits, nsu, yaws = [], 0, set()
    for hop in (0, 1):
        for mag in (80, 50, 30, 15):
            for deg in range(180, 292, 2):
                e.load(sp)
                sx, sy = stick_for(deg, mag)
                maxy, su = 0, False
                for f in range(25):
                    e.step(A_ if (hop and f < 2) else 0, sx, sy, 2)
                    q = player(e)
                    maxy = max(maxy, q['y'])
                    if q['action'] == 34 and not su:
                        su = True; nsu += 1; yaws.add(round(e.f32(PLAYER + 0x80)))
                    if H.inside(q) and maxy < 95:
                        hits.append((hop, mag, deg, f, q['x'], q['y'], q['z'], maxy, su))
                        break
    return {'pt': pt, 'start': start, 'hits': hits, 'stepups': nsu, 'yaws': sorted(yaws)}


if __name__ == '__main__':
    pts = [(-398.0 + 0.5 * i, -150.0 + 0.5 * j) for i in range(0, 15) for j in range(0, 21)]
    pts = [p for p in pts if not (p[0] < -397 and p[1] < -147)]
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    t0, res = time.time(), []
    for r in pool.imap_unordered(run, pts):
        res.append(r)
        if r['hits']:
            print('LOW ENTRY', json.dumps({'pt': r['pt'], 'start': r['start'], 'hits': r['hits'][:3]}), len(r['hits']), flush=True)
    json.dump(res, open(sys.argv[1], 'w'))
    ok = [r for r in res if r['start']]
    print('done: %d points (%d stood on the ground), %d with step-ups, %d with a low entry [%.0fs]' % (
        len(res), len(ok), sum(1 for r in ok if r['stepups']), sum(1 for r in ok if r['hits']), time.time() - t0), flush=True)
    import collections
    print('step-up yaws seen:', sorted(collections.Counter(y // 15 * 15 for r in ok for y in r['yaws']).items()))
    print('errors:', [(r['pt'], r['err']) for r in res if r.get('err')][:5])
    pool.terminate()
