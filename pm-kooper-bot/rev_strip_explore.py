"""Go-Explore from the legend corner (states/pra01_topright.st) for the reverse mirror clip: cells = Mario (x, z)/15
x Lakilester speed/10; moves = 1-8 frames of stick (16 directions, full or half) or neutral, sometimes a jump.
Whenever Mario is near the crossing strip (x 860..895, z -155..-70) and Lakilester's speed >= 60, C-down is tried
from that frame; hit = riding on the real side (z > 1). usage: rev_strip_explore.py <out_dir> <minutes>"""
import json, math, os, random, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/se%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def play(task):
    seq, test_from = task
    e = W['e']; chk = os.path.join(W['d'], 'c.st')
    e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    cells, hits, best = {}, [], 0
    for k, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        if tuple(where(e)[:2]) != (21, 0): break
        p, l = player(e), laki(e)
        if not l: break
        s = l['speed']
        cells.setdefault((round(p['x'] / 15), round(p['z'] / 15), min(int(s / 10), 15)), k)
        if k >= test_from and 860 < p['x'] < 895 and -155 < p['z'] < -70:
            best = max(best, s)
            if s >= 60 and p['action'] in (0, 1, 2):
                e.save(chk)
                e.step(CD, 0, 0, 2)
                for i in range(28): e.step(0, 0, 0, 2)
                q = player(e)
                if q['action'] == 33 and q['z'] > 1 and tuple(where(e)[:2]) == (21, 0):
                    hits.append({'frame': k, 'speed': s, 'mario': (p['x'], p['z']), 'end': (q['x'], q['y'], q['z'])})
                e.load(chk)
    return cells, hits, best
def main():
    out, minutes = sys.argv[1], float(sys.argv[2]); os.makedirs(out, exist_ok=True)
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    arch = {'seed': {'seq': [], 'n': 0, 'w': 1}}
    t0, tries, hits, top = time.time(), 0, [], 0
    while time.time() - t0 < minutes * 60:
        keys = list(arch)
        ws = [arch[k]['w'] / math.sqrt(1 + arch[k]['n']) for k in keys]
        tasks = []
        for k in random.choices(keys, weights=ws, k=64):
            arch[k]['n'] += 1
            s = list(arch[k]['seq'])
            for _ in range(random.choice((1, 2, 3))):
                if random.random() < 0.3: st = (0, 0)
                else: st = stick_for(random.choice(range(0, 360, 22)), random.choice((80, 40)))
                jump = random.random() < 0.08
                s += [((0x80 if jump and i < 8 else 0), st[0], st[1]) for i in range(random.choice((1, 2, 4, 8)))]
            tasks.append((s[:400], len(arch[k]['seq'])))
        for (s, st), (cells, h, b) in zip(tasks, pool.map(play, tasks, chunksize=4)):
            tries += 1; top = max(top, b)
            for x in h:
                x['seq'] = s[:x['frame'] + 1]; hits.append(x)
                print('HIT', json.dumps({k: x[k] for k in ('frame', 'speed', 'mario', 'end')}), flush=True)
                json.dump(hits, open(os.path.join(out, 'hits.json'), 'w'))
            for key, f in cells.items():
                if key not in arch or f + 1 < len(arch[key]['seq']):
                    near = 1 + 4 * (860 < key[0] * 15 < 895 and -155 < key[1] * 15 < -70)
                    arch[key] = {'seq': s[:f + 1], 'n': arch.get(key, {}).get('n', 0), 'w': near * (1 + key[2])}
        if tries % 1280 == 0:
            print('%d tries, %d cells, best speed with Mario in the strip %.1f, %d hits [%.0fs]' % (tries, len(arch), top, len(hits), time.time() - t0), flush=True)
    pool.terminate()
if __name__ == '__main__':
    main()
