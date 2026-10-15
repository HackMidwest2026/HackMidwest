"""blue house (mac_02) spin-jump setups.

From a standing spot, spin (Z) holding direction a for k frames, then jump (A held 12) holding (b, m) where b is
aimed from the jump spot back at the corner notch (-395, -141) plus an offset. A landing on the leaning wall face
(collider 45) is then tested with every second jump (h2, mag2, deg2 for 6 frames, then up-slightly-right 276),
counting how many get Mario inside: that count is the setup's tolerance for the second jump."""
import json, math, multiprocessing as mp, os, sys, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from corner_sweep import stick_for
A_, Z_ = 0x80, 0x20
NOTCH = (-395.0, -141.0)


def second_jumps(e, lp):
    from pm import player, GAME_MODE, GM_WORLD
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
    return ok


def run(job):
    from pm import player, COLLISION
    x0, z0, a, k = job
    e = H.W['e']
    base = H.base(x0, z0)
    e.load(base)
    p = player(e)
    if abs(p['x'] - x0) > 0.5 or abs(p['z'] - z0) > 0.5:
        return []
    sa = stick_for(a, 80)
    for f in range(k):
        e.step(Z_ if f == 0 else 0, sa[0], sa[1], 2)
    p = player(e)
    if p['action'] != 26:
        return []
    sp = os.path.join(H.W['d'], 'spin.st')
    e.save(sp)
    to = math.degrees(math.atan2(NOTCH[1] - p['z'], NOTCH[0] - p['x']))
    out = []
    for off in range(-20, 21, 4):
        for m in (15, 20, 30, 45, 80):
            b = (to + off) % 360
            e.load(sp)
            st = stick_for(b, m)
            air = False
            for f in range(45):
                e.step(A_ if f < 12 else 0, st[0], st[1], 2)
                q = player(e)
                if q['action'] in (3, 4, 5, 8, 13):
                    air = True
                elif air:
                    if e.s16(COLLISION + 2) == 45 and q['y'] > 25:
                        lp = os.path.join(H.W['d'], 'land.st')
                        e.save(lp)
                        ok = second_jumps(e, lp)
                        out.append({'job': job, 'jump_from': (p['x'], p['z']), 'b': round(b, 1), 'm': m,
                                    'land': (q['x'], q['y'], q['z']), 'ok': ok})
                    break
    return out


if __name__ == '__main__':
    jobs = [(x, z, a, k) for x in range(-430, -339, 6) for z in range(-190, -114, 6)
            for a in range(0, 360, 15) for k in (3, 5, 8)]
    print(len(jobs), 'spin setups', flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    t0, res = time.time(), []
    for i, r in enumerate(pool.imap_unordered(run, jobs, chunksize=4)):
        res += r
        for g in r:
            if g['ok']:
                print('SETUP', json.dumps({kk: g[kk] for kk in ('job', 'jump_from', 'b', 'm', 'land')}), 'second jumps OK:', len(g['ok']), flush=True)
        if (i + 1) % 1000 == 0:
            print('%d/%d, %d wall-face landings, %d with a way in [%.0fs]' % (
                i + 1, len(jobs), len(res), sum(1 for x in res if x['ok']), time.time() - t0), flush=True)
            json.dump(res, open(sys.argv[1], 'w'))
    json.dump(res, open(sys.argv[1], 'w'))
    print('done: %d landings, %d with a way in [%.0fs]' % (len(res), sum(1 for x in res if x['ok']), time.time() - t0), flush=True)
    pool.terminate()
