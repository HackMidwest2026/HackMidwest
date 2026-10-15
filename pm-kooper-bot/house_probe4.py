"""blue house (mac_02): from every distinct step-up found by house_probe2 (walking into the corner), replay to the
frame the step-up ends, then wait d frames and jump / spin-jump / hop at every stick angle."""
import json, math, multiprocessing as mp, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from corner_sweep import stick_for
import house_probe as H
A, Z = 0x0080, 0x0020


def walk_inputs(job, upto):
    x0, z0, a1, n1, a2, mag = job
    return [stick_for(a1 if f < n1 else a2, mag) for f in range(upto)]


def prep(job, end_f):
    """state at the end of the step-up (saved per worker)"""
    from pm import player
    e = H.W['e']
    e.load(H.base(job[0], job[1]))
    for sx, sy in walk_inputs(job, end_f):
        e.step(0, sx, sy, 2)
    path = os.path.join(H.W['d'], 'su.st')
    e.save(path)
    return path, player(e)


def run(task):
    from pm import player, GAME_MODE, GM_WORLD
    job, end_f = task
    e = H.W['e']
    path, p0 = prep(job, end_f)
    hits, n = [], 0
    for d in (0, 1, 2, 3, 5):
        for kind in ('jump', 'hop', 'spinjump'):
            for deg in range(0, 360, 10):
                sx, sy = stick_for(deg, 80)
                e.load(path)
                for f in range(d + 40):
                    g = f - d
                    if g < 0:
                        b = 0
                    elif kind == 'jump':
                        b = A if g < 12 else 0
                    elif kind == 'hop':
                        b = A if g < 2 else 0
                    else:
                        b = Z if g == 0 else (A if 2 <= g < 14 else 0)
                    e.step(b, sx, sy, 2)
                    if e.s16(GAME_MODE) != GM_WORLD:
                        break
                    p = player(e)
                    if H.inside(p):
                        hits.append({'job': job, 'end_f': end_f, 'd': d, 'kind': kind, 'deg': deg, 'f': f,
                                     'pos': (p['x'], p['y'], p['z']), 'start': (p0['x'], p0['y'], p0['z'])})
                        break
                n += 1
    return hits, n


def main():
    R = json.load(open(sys.argv[1]))
    tasks, seen = [], set()
    for r in R:
        if not r['stepup'] or r['inside']:
            continue
        end_f = r['stepup'][-1][0] + 1
        key = tuple(round(v) for v in r['stepup'][-1][1:4])  # where the step-up ended (1-unit cells)
        if key in seen:
            continue
        seen.add(key)
        tasks.append((r['job'], end_f))
    print(len(tasks), 'distinct step-ups', flush=True)
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    t0, tot, allh = time.time(), 0, []
    for i, (hits, n) in enumerate(pool.imap_unordered(run, tasks)):
        tot += n; allh += hits
        for h in hits[:3]:
            print('INSIDE', json.dumps(h), flush=True)
        if (i + 1) % 20 == 0:
            print('%d/%d step-ups, %d tries, %d inside [%.0fs]' % (i + 1, len(tasks), tot, len(allh), time.time() - t0), flush=True)
    json.dump(allh, open(sys.argv[2], 'w'))
    print('done %d tries, %d inside [%.0fs]' % (tot, len(allh), time.time() - t0), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
