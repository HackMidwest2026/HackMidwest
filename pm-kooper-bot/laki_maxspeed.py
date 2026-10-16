"""pra_01: how fast can Lakilester get? Go-Explore over Mario's movement (stick direction/strength, A jump, Z spin,
segments of 1-20 frames), cells by (Mario x/25, z/25, Lakilester speed/2). Reports the highest speed seen, where."""
import json, math, os, random, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
W = {}


def init():
    from emu import Emu
    d = '/dev/shm/pmbot/lm%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'] = Emu(os.environ['PM_ROM'], d)


def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n


def play(seq):
    e = W['e']
    e.load('states/pra01_start.st')
    best, cells = (0, None), {}
    for f, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        if e.s16(GAME_MODE) != GM_WORLD or tuple(where(e)[:2]) != (21, 0):
            break
        p, l = player(e), laki(e)
        if not l: break
        s = l['speed']
        if s > best[0]:
            best = (s, f, round(p['x'], 1), round(p['z'], 1), round(l['x'], 1), round(l['z'], 1))
        cells.setdefault((round(p['x'] / 25), round(p['z'] / 25), min(int(s / 2), 40)), f)
    return best, cells


def seg():
    deg = random.choice([None] + list(range(0, 360, 30)))
    sx, sy = stick_for(deg, random.choice((80, 40))) if deg is not None else (0, 0)
    kind = random.choice(('none', 'none', 'spin', 'jump'))
    n = random.choice((1, 2, 4, 8, 12, 20))
    return [({'spin': 0x20, 'jump': 0x80}.get(kind, 0) if i == 0 else (0x80 if kind == 'jump' and i < 10 else 0), sx, sy) for i in range(n)]


if __name__ == '__main__':
    hours = float(sys.argv[1])
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    arch = {('seed',): {'seq': [], 'n': 0}}
    t0, top, tries = time.time(), (0, None), 0
    while time.time() - t0 < hours * 3600:
        keys = list(arch)
        ws = [(1 + k[2] if len(k) == 3 else 1) / math.sqrt(1 + arch[k]['n']) for k in keys]
        seqs = []
        for k in random.choices(keys, weights=ws, k=64):
            arch[k]['n'] += 1
            s = list(arch[k]['seq'])
            for _ in range(random.choice((1, 2))): s += seg()
            seqs.append(s[:400])
        for s, (best, cells) in zip(seqs, pool.map(play, seqs, chunksize=4)):
            tries += 1
            if best[0] > top[0]:
                top = best + (None,)
                json.dump({'best': best, 'seq': s[:best[1] + 1]}, open(os.environ.get('OUT', 'laki_maxspeed.json'), 'w'))
                print('new max speed %.2f at frame %d: mario (%s, %s) laki (%s, %s) [%.0fs]' % (best + (time.time() - t0,)), flush=True)
            for key, f in cells.items():
                if key not in arch or f + 1 < len(arch[key]['seq']):
                    arch[key] = {'seq': s[:f + 1], 'n': arch.get(key, {}).get('n', 0)}
        if tries % 1024 == 0:
            print('%d tries, %d cells, max speed %.2f [%.0fs]' % (tries, len(arch), top[0], time.time() - t0), flush=True)
    pool.terminate()
