"""Brute force for the reverse mirror clip: maximize Lakilester's speed at the mount while Mario stands in the stair
strip (x 872..884, z -144..-72; any speed 120..190 crosses there). Go-Explore from START (default
states/pra01_topright_fast.st): moves = 1-12 frames of stick (24 directions, full/half) or neutral, 10% with a jump.
Cells = Mario (x/12, z/12, y/10) x Lakilester (x/60, z/60) x speed/10. Selection favours cells near the strip with a
fast Lakilester. Every frame Mario is in the strip with Lakilester >= 60, C-down is tried; the mount speed is
recorded, hit = riding on the real side. usage: rev_brute.py <out_dir> <minutes>"""
import json, math, os, random, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
START = os.environ.get('START', 'states/pra01_topright_fast.st')
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/bf%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def in_strip(p): return 872 <= p['x'] <= 884 and -144 <= p['z'] <= -72
def near_strip(x, z): return 840 <= x <= 920 and -180 <= z <= -40
def play(task):
    seq, test_from = task
    e = W['e']; chk = os.path.join(W['d'], 'c.st')
    e.load(START); e.step(0, 0, 0, 2)
    cells, hits, best = {}, [], (0, None)
    for k, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        if tuple(where(e)[:2]) != (21, 0): break
        p, l = player(e), laki(e)
        if not l: break
        s = l['speed']
        key = (round(p['x'] / 12), round(p['z'] / 12), round(p['y'] / 10), round(l['x'] / 60), round(l['z'] / 60), min(int(s / 10), 20))
        cells.setdefault(key, k)
        if k >= test_from and in_strip(p) and p['action'] in (0, 1, 2) and s >= 60:
            e.save(chk)
            e.step(CD, sx, sy, 2)
            ms, last = None, 0
            for i in range(30):
                if ms is None and player(e)['action'] == 33: ms = last
                ll = laki(e); last = ll['speed'] if ll else 0
                e.step(0, 0, 0, 2)
            q = player(e)
            if ms and ms > best[0]: best = (ms, k)
            if q['action'] == 33 and q['z'] > 1 and tuple(where(e)[:2]) == (21, 0):
                hits.append({'frame': k, 'mount_speed': ms, 'mario': (p['x'], p['y'], p['z']), 'end': (q['x'], q['y'], q['z'])})
            e.load(chk)
    return cells, hits, best
def main():
    out, minutes = sys.argv[1], float(sys.argv[2]); os.makedirs(out, exist_ok=True)
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    arch = {'seed': {'seq': [], 'n': 0, 'w': 1.0}}
    t0, tries, hits, top = time.time(), 0, [], (0, None)
    while time.time() - t0 < minutes * 60:
        keys = list(arch)
        ws = [arch[k]['w'] / math.sqrt(1 + arch[k]['n']) for k in keys]
        tasks = []
        for k in random.choices(keys, weights=ws, k=64):
            arch[k]['n'] += 1
            s = list(arch[k]['seq'])
            for _ in range(random.choice((1, 2, 3))):
                st = (0, 0) if random.random() < 0.25 else stick_for(random.choice(range(0, 360, 15)), random.choice((80, 80, 40)))
                jump = random.random() < 0.1
                s += [((0x80 if jump and i < 8 else 0), st[0], st[1]) for i in range(random.choice((1, 2, 4, 8, 12)))]
            tasks.append((s[:300], len(arch[k]['seq'])))
        for (s, st), (cells, h, b) in zip(tasks, pool.map(play, tasks, chunksize=4)):
            tries += 1
            if b[0] > top[0]:
                top = (b[0], s[:b[1] + 1])
                json.dump({'mount_speed': top[0], 'seq': top[1]}, open(os.path.join(out, 'best.json'), 'w'))
            for x in h:
                x['seq'] = s[:x['frame'] + 1]; hits.append(x)
                print('HIT', json.dumps({k: x[k] for k in ('frame', 'mount_speed', 'mario', 'end')}), flush=True)
                json.dump(hits, open(os.path.join(out, 'hits.json'), 'w'))
            for key, f in cells.items():
                if key not in arch or f + 1 < len(arch[key]['seq']):
                    x, z = key[0] * 12, key[1] * 12
                    w = (1 + key[5]) ** 2 * (6 if near_strip(x, z) else 1)
                    arch[key] = {'seq': s[:f + 1], 'n': arch.get(key, {}).get('n', 0), 'w': w}
        if tries % 640 == 0:
            print('%d tries, %d cells, best mount speed in the strip %.1f, %d hits [%.0fs]' % (tries, len(arch), top[0], len(hits), time.time() - t0), flush=True)
    pool.terminate()
if __name__ == '__main__':
    main()
