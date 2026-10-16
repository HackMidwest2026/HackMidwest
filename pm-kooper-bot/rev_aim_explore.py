"""pra_01 reflected side: where can an idle (stale-history) Lakilester be pushed? Go-Explore where a move is one
stop-and-go cycle (go G = 1 or 2 frames, stop 2) with the stick aimed at Lakilester rotated by THETA degrees
(-60..60), so the push direction can bend into an arc. Kept only while Lakilester stays idle (speed 0) and Mario
within the 40-unit tether. Cells: Lakilester (x, z)/10. Reports the reachable extent; saves arch.json.
usage: python3 rev_aim_explore.py <out_dir> <minutes> [seed_state]"""
import json, math, os, random, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
W = {}
SEED = sys.argv[3] if len(sys.argv) > 3 else 'states/pra01_top_rock.st'
THETAS = [-60, -40, -25, -12, 0, 12, 25, 40, 60]


def init(seed):
    from emu import Emu
    d = '/dev/shm/pmbot/ax%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['seed'] = Emu(os.environ['PM_ROM'], d), seed


def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n


def play(seq):
    e = W['e']
    e.load(W['seed']); e.step(0, 0, 0, 2)
    cells = {}
    for k, (g, th) in enumerate(seq):
        p, l = player(e), laki(e)
        deg = math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th
        sx, sy = stick_for(deg % 360, 80)
        for i in range(g): e.step(0, sx, sy, 2)
        e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
        if tuple(where(e)[:2]) != (21, 0): break
        p, l = player(e), laki(e)
        if l['speed'] > 0.01 or math.hypot(p['x'] - l['x'], p['z'] - l['z']) > 40: break
        cells.setdefault((round(l['x'] / 10), round(l['z'] / 10)), (k, l['x'], l['z'], p['x'], p['z']))
    return cells


if __name__ == '__main__':
    out_dir, minutes = sys.argv[1], float(sys.argv[2])
    os.makedirs(out_dir, exist_ok=True)
    pool = mp.get_context('spawn').Pool(4, initializer=init, initargs=(SEED,))
    arch = {'seed': {'seq': [], 'n': 0, 'lx': 0, 'lz': 0}}
    t0, tries = time.time(), 0
    while time.time() - t0 < minutes * 60:
        keys = list(arch)
        ws = [1 / math.sqrt(1 + arch[k]['n']) for k in keys]
        tasks = []
        for k in random.choices(keys, weights=ws, k=64):
            arch[k]['n'] += 1
            s = list(arch[k]['seq'])
            th = random.choice(THETAS)
            for _ in range(random.choice((1, 2, 4, 8, 16))):
                if random.random() < 0.3: th = random.choice(THETAS)
                s.append((random.choice((1, 1, 2)), th))
            tasks.append(s)
        for s, cells in zip(tasks, pool.map(play, tasks, chunksize=4)):
            tries += 1
            for key, (k, lx, lz, mx, mz) in cells.items():
                key = str(key)
                if key not in arch or k + 1 < len(arch[key]['seq']):
                    arch[key] = {'seq': s[:k + 1], 'n': arch.get(key, {}).get('n', 0), 'lx': lx, 'lz': lz, 'mx': mx, 'mz': mz}
        if tries % 640 == 0:
            xs = [a['lx'] for k, a in arch.items() if k != 'seed']
            zs = [a['lz'] for k, a in arch.items() if k != 'seed']
            far = max((a for k, a in arch.items() if k != 'seed'), key=lambda a: math.hypot(a['lx'] - 594, a['lz'] + 13))
            print('%d tries, %d cells, laki x %.0f..%.0f z %.0f..%.0f, farthest from start (%.0f, %.0f) [%.0fs]' % (tries, len(arch), min(xs), max(xs), min(zs), max(zs), far['lx'], far['lz'], time.time() - t0), flush=True)
            json.dump(arch, open(os.path.join(out_dir, 'arch.json'), 'w'))
    pool.terminate()
