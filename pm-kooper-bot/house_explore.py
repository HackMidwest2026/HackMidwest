"""Go-Explore at the blue house's front-right corner (mac_02).

Each archive entry is an input sequence replayed from one base state (Mario standing near the corner).
A try appends one random segment (stick angle, strength, buttons, length) and records every frame's cell
(x, y/2, z rounded, airborne). Cells far from the corner are dropped. Goal: Mario inside the house box,
or above y = 100 (over the two-sided part of the wall)."""
import json, math, multiprocessing as mp, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from corner_sweep import stick_for
import house_probe as H
A, Z = 0x0080, 0x0020
BASES = [(-380.0, -128.0), (-375.0, -150.0), (-390.0, -125.0)]


def near(p):
    return -420 < p['x'] < -360 and -175 < p['z'] < -110


def play(task):
    from pm import player, GAME_MODE, GM_WORLD
    bi, seq = task
    e = H.W['e']
    e.load(H.base(*BASES[bi]))
    cells, f, best = {}, 0, None
    for b, deg, mag, n in seq:
        sx, sy = stick_for(deg, mag) if deg is not None else (0, 0)
        for i in range(n):
            bb = b
            if b == 'tap':
                bb = A if i == 0 else 0
            elif b == 'spin':
                bb = Z if i == 0 else 0
            elif b == 'hold':
                bb = A
            e.step(bb, sx, sy, 2)
            f += 1
            if e.s16(GAME_MODE) != GM_WORLD:
                return {'cells': cells, 'goal': None, 'dead': True}
            p = player(e)
            if H.inside(p) or p['y'] > 100:
                return {'cells': cells, 'goal': (f, p['x'], p['y'], p['z'], p['action']), 'dead': False}
            if not near(p):
                continue
            key = (round(p['x']), round(p['y'] / 2), round(p['z']), p['action'] in (3, 4, 5, 8, 13, 34))
            cells[key] = f          # earliest frame within this sequence reaching it
    return {'cells': cells, 'goal': None, 'dead': False}


def rand_seg():
    deg = random.choice([None] + list(range(0, 360, 15)))
    mag = random.choice((80, 80, 40, 20))
    b = random.choice((0, 0, 'tap', 'hold', 'hold', 'spin'))
    n = random.choice((1, 1, 2, 3, 5, 8, 12))
    return (b, deg, mag, n)


def main():
    out_dir = sys.argv[1]
    hours = float(sys.argv[2])
    os.makedirs(out_dir, exist_ok=True)
    pool = mp.get_context('spawn').Pool(4, initializer=H.init)
    archive = {}                                         # cell -> {'bi','seq','visits','y'}
    for bi in range(len(BASES)):
        archive[('base', bi)] = {'bi': bi, 'seq': [], 'visits': 0, 'y': 20}
    t0, tries, goals, maxy = time.time(), 0, [], 0
    while time.time() - t0 < hours * 3600:
        keys = list(archive)
        # weight: rarely tried cells, high cells, cells close to the corner notch
        def w(k):
            a = archive[k]
            yb = 1 + max(0, a['y'] - 20) / 5
            return yb / math.sqrt(1 + a['visits'])
        ws = [w(k) for k in keys]
        picks = random.choices(keys, weights=ws, k=64)
        tasks = []
        for k in picks:
            a = archive[k]
            a['visits'] += 1
            seq = a['seq'] + [rand_seg() for _ in range(random.choice((1, 1, 2, 3)))]
            tasks.append((a['bi'], seq))
        for (bi, seq), r in zip(tasks, pool.map(play, tasks, chunksize=4)):
            tries += 1
            if r['goal']:
                goals.append({'bi': bi, 'seq': seq, 'goal': r['goal']})
                print('GOAL', json.dumps(goals[-1]), flush=True)
                json.dump(goals, open(os.path.join(out_dir, 'goals.json'), 'w'))
            for key, f in r['cells'].items():
                # truncate the sequence to the segment that reached the cell
                cut, acc = [], 0
                for s in seq:
                    cut.append(s)
                    acc += s[3]
                    if acc >= f:
                        break
                if key not in archive or sum(s[3] for s in cut) < sum(s[3] for s in archive[key]['seq']):
                    old = archive.get(key, {}).get('visits', 0)
                    archive[key] = {'bi': bi, 'seq': cut, 'visits': old, 'y': key[1] * 2}
                    maxy = max(maxy, key[1] * 2)
        if tries % 2048 == 0:
            print('%d tries, %d cells, max y near corner %.0f, goals %d [%.0fs]' % (
                tries, len(archive), maxy, len(goals), time.time() - t0), flush=True)
            json.dump([[list(map(str, k)), v] for k, v in archive.items()], open(os.path.join(out_dir, 'archive.json'), 'w'))
    print('done', tries, len(goals), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
