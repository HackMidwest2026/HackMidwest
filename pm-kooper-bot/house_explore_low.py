"""Go-Explore for a LOW way into the blue house (mac_02): Mario must end inside the house box without ever going
above y = 95 (so the open top of the wall doesn't count).

Sequences are per-frame input lists replayed from one base state (Mario pressed against the house front at x -406).
Seeds: standing there, and the human-style setup (house_setup_tol) up to its wall-face landing. Cells are
half-unit (x, z), 2-unit y and airborne/grounded, kept only near the front-right corner."""
import json, math, multiprocessing as mp, os, random, sys, time
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
import house_setup_tol as T
from corner_sweep import stick_for
A_, Z_ = 0x80, 0x20
YMAX = 95.0


def seed_setup():
    sa, sl = stick_for(340, 80), stick_for(150, 80)
    seq = [(Z_ if f == 0 else 0, sa[0], sa[1]) for f in range(9)]
    seq += [(A_ if f < 12 else 0,) + (sl if f < 10 else (0, 0)) for f in range(14)]
    return seq


def near(p):
    return -412 < p['x'] < -372 and -165 < p['z'] < -118


def play(seq):
    from pm import player, GAME_MODE, GM_WORLD
    e = H.W['e']
    e.load(T.stand_at_front(-406))
    cells, maxy = {}, 0
    for f, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        if e.s16(GAME_MODE) != GM_WORLD:
            return {'cells': cells, 'goal': None}
        p = player(e)
        maxy = max(maxy, p['y'])
        if maxy > YMAX:
            return {'cells': cells, 'goal': None}
        if H.inside(p):
            return {'cells': cells, 'goal': (f, p['x'], p['y'], p['z'], p['action'], maxy)}
        if near(p):
            key = (round(p['x'] * 2), round(p['y'] / 2), round(p['z'] * 2), p['action'] in (3, 4, 5, 8, 13, 34))
            cells.setdefault(key, f)
    return {'cells': cells, 'goal': None}


def rand_seg():
    deg = random.choice([None] + list(range(0, 360, 10)))
    mag = random.choice((80, 60, 40, 25, 15))
    kind = random.choice(('none', 'none', 'tap', 'hold', 'hold', 'spin', 'hop'))
    n = random.choice((1, 1, 1, 2, 2, 3, 4, 6, 9, 12))
    sx, sy = stick_for(deg, mag) if deg is not None else (0, 0)
    out = []
    for i in range(n):
        b = {'tap': A_ if i == 0 else 0, 'hold': A_, 'spin': Z_ if i == 0 else 0, 'hop': A_ if i < 2 else 0}.get(kind, 0)
        out.append((b, sx, sy))
    return out


def main():
    out_dir, hours = sys.argv[1], float(sys.argv[2])
    os.makedirs(out_dir, exist_ok=True)
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    archive = {('seed', 0): {'seq': [], 'visits': 0, 'score': 1.0}, ('seed', 1): {'seq': seed_setup(), 'visits': 0, 'score': 3.0}}
    t0, tries, goals = time.time(), 0, []
    while time.time() - t0 < hours * 3600:
        keys = list(archive)
        ws = [archive[k]['score'] / math.sqrt(1 + archive[k]['visits']) for k in keys]
        picks = random.choices(keys, weights=ws, k=64)
        seqs = []
        for k in picks:
            archive[k]['visits'] += 1
            s = list(archive[k]['seq'])
            for _ in range(random.choice((1, 1, 2, 3))):
                s += rand_seg()
            seqs.append(s)
        for s, r in zip(seqs, pool.map(play, seqs, chunksize=4)):
            tries += 1
            if r['goal']:
                goals.append({'seq': s[:r['goal'][0] + 1], 'goal': r['goal']})
                print('GOAL', json.dumps(r['goal']), len(goals[-1]['seq']), 'frames', flush=True)
                json.dump(goals, open(os.path.join(out_dir, 'goals.json'), 'w'))
            for key, f in r['cells'].items():
                cut = s[:f + 1]
                if key not in archive or len(cut) < len(archive[key]['seq']):
                    # favour cells in the notch (just east of x -397, close to the front wall line z -147)
                    x, z = key[0] / 2, key[2] / 2
                    notch = math.exp(-(((x + 395.5) / 3) ** 2 + ((z + 144) / 5) ** 2))
                    archive[key] = {'seq': cut, 'visits': archive.get(key, {}).get('visits', 0), 'score': 1 + 6 * notch}
        if tries % 2048 == 0:
            best = min((k for k in archive if k[0] != 'seed'), key=lambda k: k[2], default=None)
            print('%d tries, %d cells, smallest z near corner %s, goals %d [%.0fs]' % (
                tries, len(archive), best and best[2] / 2, len(goals), time.time() - t0), flush=True)
    print('done', tries, len(goals), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
