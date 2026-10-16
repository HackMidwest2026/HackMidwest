"""pra_01 reflected side, the legend's arc push, as a Go-Explore search.

Seed: states/pra01_top_rock.st (Mario at the bottom of the mirror by the left rock, (555.4, -13), Lakilester on
his right facing left). A move is one stop-and-go cycle: go G (1 or 2) frames with the stick in one of 16
directions, then stop 2 frames. A state is kept only if Lakilester is still idle (speed 0) at the end of the
cycle, i.e. he is being pushed with a stale history pointer. Cells: Lakilester (x, z)/15 and Mario (x, z)/15.
Every new cell with Lakilester x >= 760 gets the release test: hold down (or down-left/down-right) and press
C-down on each frame 0..45 in turn; hit = Mario riding Lakilester on the real side (z > 1) in pra_01.
usage: python3 rev_arc_explore.py <out_dir> <hours>"""
import json, math, os, random, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
SEED = 'states/pra01_top_rock.st'
RELEASES = [(90, 80), (60, 80), (120, 80), (90, 40)]
W = {}


def init():
    from emu import Emu
    d = '/dev/shm/pmbot/ae%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d


def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n


def release_test(e, base, deg, mag):
    sx, sy = stick_for(deg, mag)
    hits, top = [], 0
    for f in range(46):
        e.load(base); e.step(0, 0, 0, 2)
        for i in range(f): e.step(0, sx, sy, 2)
        e.step(CD, sx, sy, 2)
        for i in range(28):
            if player(e)['action'] != 33:
                l = laki(e)
                if l: top = max(top, l['speed'])
            e.step(0, 0, 0, 2)
        p = player(e)
        if p['action'] == 33 and p['z'] > 1 and tuple(where(e)[:2]) == (21, 0) and p['y'] > -100:
            hits.append({'release': (deg, mag), 'cd_frame': f, 'end': (round(p['x'], 1), round(p['y'], 1), round(p['z'], 1))})
    return hits, top


def play(task):
    seq, test_from = task
    e = W['e']
    e.load(SEED)
    e.step(0, 0, 0, 2)
    cells, hits, tops = {}, [], []
    for k, (g, deg) in enumerate(seq):
        sx, sy = stick_for(deg, 80)
        for i in range(g): e.step(0, sx, sy, 2)
        e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
        if tuple(where(e)[:2]) != (21, 0): break
        p, l = player(e), laki(e)
        if not l or l['speed'] > 0.01: break
        key = (round(l['x'] / 15), round(l['z'] / 15), round(p['x'] / 15), round(p['z'] / 15))
        cells.setdefault(key, (k, l['x'], l['z']))
        if k >= test_from and l['x'] >= 760 and key not in W.setdefault('tested', set()):
            W['tested'].add(key)
            base = os.path.join(W['d'], 'base.st'); e.save(base)
            for deg2, mag in RELEASES:
                h, t = release_test(e, base, deg2, mag)
                tops.append(t)
                for x in h:
                    x['seq'] = seq[:k + 1]; x['laki'] = (l['x'], l['z']); x['mario'] = (p['x'], p['z'])
                    hits.append(x)
            e.load(base); e.step(0, 0, 0, 2)
    return cells, hits, max(tops) if tops else 0


def main():
    out_dir, hours = sys.argv[1], float(sys.argv[2])
    os.makedirs(out_dir, exist_ok=True)
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    arch = {'seed': {'seq': [], 'n': 0, 'lx': 594, 'lz': -13}}
    t0, tries, hits, top, best = time.time(), 0, [], 0, (0, None)
    while time.time() - t0 < hours * 3600:
        keys = list(arch)
        # favour cells with Lakilester far right and far north (the top-right corner), and rarely tried
        ws = [math.exp((arch[k]['lx'] - 600) / 120 + (-arch[k]['lz']) / 150) / math.sqrt(1 + arch[k]['n']) for k in keys]
        tasks = []
        for k in random.choices(keys, weights=ws, k=32):
            a = arch[k]; a['n'] += 1
            s = list(a['seq'])
            for _ in range(random.choice((1, 2, 4, 8))):
                s.append((random.choice((1, 1, 2)), random.choice(range(0, 360, 15))))
            tasks.append((s, len(a['seq'])))
        for (s, st), (cells, h, tp) in zip(tasks, pool.map(play, tasks, chunksize=2)):
            tries += 1
            top = max(top, tp)
            for x in h:
                hits.append(x)
                print('HIT', json.dumps({k: x[k] for k in ('release', 'cd_frame', 'end', 'laki', 'mario')}), 'cycles', len(x['seq']), flush=True)
                json.dump(hits, open(os.path.join(out_dir, 'hits.json'), 'w'))
            for key, (k, lx, lz) in cells.items():
                if key not in arch or k + 1 < len(arch[key]['seq']):
                    arch[key] = {'seq': s[:k + 1], 'n': arch.get(key, {}).get('n', 0), 'lx': lx, 'lz': lz}
                    if lx - lz > best[0]: best = (lx - lz, (round(lx, 1), round(lz, 1)), k + 1)
        if tries % 256 == 0:
            print('%d tries, %d cells, furthest Lakilester %s after %s cycles, top release speed %.1f, %d hits [%.0fs]' % (tries, len(arch), best[1], best[2], top, len(hits), time.time() - t0), flush=True)
            json.dump({str(k): v for k, v in arch.items()}, open(os.path.join(out_dir, 'arch.json'), 'w'))
    pool.terminate()


if __name__ == '__main__':
    main()
