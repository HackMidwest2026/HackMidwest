"""blue house (mac_02) setup search along the east wall.

Mario stands against the house's east wall (x = -384, pushed out by the wall) at z0, jumps (A held h frames)
holding (deg1, mag1). If he lands on the leaning wall face he jumps again (A held h2) holding (deg2, mag2) for 6
frames, then holds up-slightly-right (276, full) for the rest. Records every combination that ends inside."""
import json, multiprocessing as mp, os, sys, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from corner_sweep import stick_for
A_ = 0x80


def landing(e, deg, mag, h):
    """first jump; returns frames used if Mario lands on the wall face, else None"""
    from pm import player, COLLISION
    st = stick_for(deg, mag)
    air = False
    for f in range(40):
        e.step(A_ if f < h else 0, st[0], st[1], 2)
        q = player(e)
        if q['action'] in (3, 4, 5, 8):
            air = True
        elif air:
            return (f, q) if (e.s16(COLLISION + 2) == 45 and q['y'] > 25) else None
    return None


def run(job):
    from pm import player, GAME_MODE, GM_WORLD
    z0 = job
    e = H.W['e']
    base = H.base(-384.0, z0)
    e.load(base)
    out = []
    for h in (12, 6, 3):
        for mag in (80, 60, 40, 25, 15):
            for deg in range(110, 211, 2):
                e.load(base)
                r = landing(e, deg, mag, h)
                if not r:
                    continue
                f1, q = r
                lp = os.path.join(H.W['d'], 'land.st')
                e.save(lp)
                ok = []
                for h2 in (12, 6, 3):
                    for mag2 in (80, 40, 20):
                        for deg2 in range(250, 341, 2):
                            e.load(lp)
                            for f in range(80):
                                st = stick_for(deg2, mag2) if f < 6 else stick_for(276, 80)
                                e.step(A_ if f < h2 else 0, st[0], st[1], 2)
                                if e.s16(GAME_MODE) != GM_WORLD:
                                    break
                                if H.inside(player(e)):
                                    ok.append((h2, mag2, deg2))
                                    break
                out.append({'z0': z0, 'h': h, 'mag': mag, 'deg': deg, 'land': (q['x'], q['y'], q['z']), 'ok': ok})
    return out


if __name__ == '__main__':
    jobs = [float(z) for z in range(-200, -147)]
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    t0, res = time.time(), []
    for i, r in enumerate(pool.imap_unordered(run, jobs)):
        res += r
        good = [x for x in r if x['ok']]
        for g in good[:3]:
            print('SETUP', json.dumps({k: g[k] for k in ('z0', 'h', 'mag', 'deg', 'land')}), 'second jumps that work:', len(g['ok']), flush=True)
        print('%d/%d z0, %d landings, %d with a way in [%.0fs]' % (i + 1, len(jobs), len(res), sum(1 for x in res if x['ok']), time.time() - t0), flush=True)
        json.dump(res, open(sys.argv[1], 'w'))
    print('done', flush=True)
    pool.terminate()
