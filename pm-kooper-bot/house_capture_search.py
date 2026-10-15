"""best-first search for a LOW entry into the blue house (mac_02), guided by the capture region.

The game pushes Mario inside once his center is at z <= -147.25 and x <= xcap(y), xcap(y) ~ -396.25 + 0.1 (y - 20)
(house_capture.py). Score of a state = how far it is from that region; the search keeps the best states per
half-unit cell and expands them with short random input segments. Goal: inside, max y < 95."""
import json, math, multiprocessing as mp, os, random, sys, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
import house_setup_tol as T
from corner_sweep import stick_for
from pm import *
A_, Z_ = 0x80, 0x20
SEEDS = [('hug', (-394.78, -146.99)), ('notch', (-395.6, -143.0)), ('notch2', (-395.5, -146.5)), ('front', (-392.0, -140.0))]


def dist(p):
    xcap = -396.25 + 0.1 * (p['y'] - 20)
    return max(p['z'] + 147.25, 0) + max(p['x'] - xcap, 0)


def setup_seed():
    sa, sl = stick_for(340, 80), stick_for(150, 80)
    seq = [(Z_ if f == 0 else 0, sa[0], sa[1]) for f in range(9)]
    seq += [(A_ if f < 12 else 0,) + (sl if f < 10 else (0, 0)) for f in range(14)]
    return seq


def play(task):
    si, seq = task
    e = H.W['e']
    if si < len(SEEDS):
        e.load(H.base(*SEEDS[si][1]))
    else:
        e.load(T.stand_at_front(-406))
    out, maxy = [], 0
    for f, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        if e.s16(GAME_MODE) != GM_WORLD:
            break
        p = player(e)
        maxy = max(maxy, p['y'])
        if maxy > 95:
            break
        if H.inside(p):
            return {'goal': (f, p['x'], p['y'], p['z'], maxy), 'cells': out}
        if -405 < p['x'] < -380 and -160 < p['z'] < -125:
            out.append((f, round(p['x'] * 4), round(p['y'] / 2), round(p['z'] * 4), p['action'] in (3, 4, 5, 8, 13, 34), dist(p)))
    return {'goal': None, 'cells': out}


def seg():
    deg = random.choice([None] + list(range(0, 360, 15)))
    mag = random.choice((80, 50, 30, 18, 10))
    kind = random.choice(('none', 'none', 'none', 'tap', 'hold', 'spin'))
    n = random.choice((1, 1, 1, 1, 2, 2, 3, 5, 8))
    sx, sy = stick_for(deg, mag) if deg is not None else (0, 0)
    return [({'tap': A_ if i == 0 else 0, 'hold': A_, 'spin': Z_ if i == 0 else 0}.get(kind, 0), sx, sy) for i in range(n)]


def main():
    out_dir, hours = sys.argv[1], float(sys.argv[2])
    os.makedirs(out_dir, exist_ok=True)
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    arch = {('seed', i): {'si': i, 'seq': [], 'd': 1.0, 'n': 0} for i in range(len(SEEDS))}
    arch[('seed', 99)] = {'si': 99, 'seq': setup_seed(), 'd': 1.0, 'n': 0}
    t0, tries, goals, best = time.time(), 0, [], 9e9
    while time.time() - t0 < hours * 3600:
        keys = list(arch)
        ws = [math.exp(-arch[k]['d'] / 0.5) / math.sqrt(1 + arch[k]['n']) + 1e-4 for k in keys]
        tasks = []
        for k in random.choices(keys, weights=ws, k=64):
            arch[k]['n'] += 1
            s = list(arch[k]['seq'])
            for _ in range(random.choice((1, 1, 2))):
                s += seg()
            tasks.append((arch[k]['si'], s))
        for (si, s), r in zip(tasks, pool.map(play, tasks, chunksize=4)):
            tries += 1
            if r['goal']:
                goals.append({'si': si, 'seq': s[:r['goal'][0] + 1], 'goal': r['goal']})
                print('GOAL', si, json.dumps(r['goal']), flush=True)
                json.dump(goals, open(os.path.join(out_dir, 'goals.json'), 'w'))
            for f, cx, cy, cz, air, d in r['cells']:
                key = (cx, cy, cz, air)
                if key not in arch or d < arch[key]['d'] - 1e-6 or (abs(d - arch[key]['d']) < 1e-6 and f + 1 < len(arch[key]['seq'])):
                    arch[key] = {'si': si, 'seq': s[:f + 1], 'd': d, 'n': arch.get(key, {}).get('n', 0)}
                    best = min(best, d)
        if tries % 2048 == 0:
            print('%d tries, %d cells, closest to capture %.3f, goals %d [%.0fs]' % (tries, len(arch), best, len(goals), time.time() - t0), flush=True)
            top = sorted(arch.items(), key=lambda kv: kv[1]['d'])[:20]
            json.dump([[list(map(str, k)), v] for k, v in top], open(os.path.join(out_dir, 'top.json'), 'w'))
    print('done', tries, len(goals), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
