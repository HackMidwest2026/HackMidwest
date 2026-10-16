"""Go-Explore for the (reverse) mirror clip in pra_01, built around the stop-and-go push.

Seeds: Mario on the real side (states/pra01_start.st) and on the reflected side (states/pra01_top_start.st), both
with Lakilester out. A try appends a few segments: walk/run in one of 8 directions for 1-8 frames, or stand still
for 1-5 frames (the stop-and-go push), occasionally a spin. Every frame where Lakilester's speed is at least
CD_MIN, C-down is tried from that exact frame; a hit is Mario riding Lakilester on the other side of the mirror
(z sign flipped, inside the room). Cells: Mario (x, z)/20, Lakilester (x, z)/20, Lakilester speed/2.
usage: python3 mirror_explore.py <out_dir> <hours>"""
import json, math, os, random, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
CD_MIN = float(os.environ.get('CD_MIN', '7'))
SEEDS = ['states/pra01_start.st', 'states/pra01_top_start.st']
W = {}


def init():
    from emu import Emu
    d = '/dev/shm/pmbot/mx%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d


def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n


def in_room(p):
    return 400 < p['x'] < 1050 and -225 < p['z'] < 225 and p['y'] > -100


def try_cd(e, side):
    """C-down from the current state; True if Mario ends riding on the other side of the mirror"""
    e.step(CD, 0, 0, 2)
    for f in range(24):
        e.step(0, 0, 0, 2)
        if e.s16(GAME_MODE) != GM_WORLD or tuple(where(e)[:2]) != (21, 0):
            return None
    p = player(e)
    if p['action'] == 33 and in_room(p) and (p['z'] > 0) != side and abs(p['z']) > 1:
        return (round(p['x'], 2), round(p['y'], 2), round(p['z'], 2))
    return None


def play(task):
    si, seq, start_test = task
    e = W['e']
    e.load(SEEDS[si])
    side = None
    cells, hits, maxspd = {}, [], 0
    chk = os.path.join(W['d'], 'chk.st')
    for f, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        if e.s16(GAME_MODE) != GM_WORLD or tuple(where(e)[:2]) != (21, 0):
            break
        p, l = player(e), laki(e)
        if not l:
            break
        if side is None:
            side = p['z'] > 0
        s = l['speed']
        maxspd = max(maxspd, s)
        cells.setdefault((si, round(p['x'] / 20), round(p['z'] / 20), round(l['x'] / 20), round(l['z'] / 20), min(int(s / 2), 30)), f)
        if f >= start_test and s >= CD_MIN and p['action'] in (0, 1, 2):
            e.save(chk)
            r = try_cd(e, side)
            if r:
                hits.append({'si': si, 'frame': f, 'speed': s, 'mario_before': (p['x'], p['y'], p['z']),
                             'laki_before': (l['x'], l['y'], l['z']), 'end': r})
            e.load(chk)
    return cells, hits, maxspd


def seg():
    if random.random() < 0.4:
        return [(0, 0, 0)] * random.choice((1, 1, 2, 3, 5))
    deg = random.choice(range(0, 360, 45))
    sx, sy = stick_for(deg, random.choice((80, 40, 20)))
    b = 0x20 if random.random() < 0.08 else 0
    return [(b if i == 0 else 0, sx, sy) for i in range(random.choice((1, 2, 3, 5, 8)))]


def main():
    out_dir, hours = sys.argv[1], float(sys.argv[2])
    os.makedirs(out_dir, exist_ok=True)
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    arch = {('seed', i): {'si': i, 'seq': [], 'n': 0, 'spd': 0} for i in range(len(SEEDS))}
    t0, tries, top, hits = time.time(), 0, 0, []
    while time.time() - t0 < hours * 3600:
        keys = list(arch)
        ws = [(1 + arch[k]['spd']) / math.sqrt(1 + arch[k]['n']) for k in keys]
        tasks = []
        for k in random.choices(keys, weights=ws, k=64):
            a = arch[k]; a['n'] += 1
            s = list(a['seq'])
            for _ in range(random.choice((1, 2, 3, 4))): s += seg()
            tasks.append((a['si'], s[:600], len(a['seq'])))
        for (si, s, st), (cells, h, mx) in zip(tasks, pool.map(play, tasks, chunksize=4)):
            tries += 1
            top = max(top, mx)
            for x in h:
                x['seq'] = s[:x['frame'] + 1]
                hits.append(x)
                print('HIT', json.dumps({k: x[k] for k in ('si', 'frame', 'speed', 'mario_before', 'laki_before', 'end')}), flush=True)
                json.dump(hits, open(os.path.join(out_dir, 'hits.json'), 'w'))
            for key, f in cells.items():
                if key not in arch or f + 1 < len(arch[key]['seq']):
                    arch[key] = {'si': si, 'seq': s[:f + 1], 'n': arch.get(key, {}).get('n', 0), 'spd': key[-1]}
        if tries % 1024 == 0:
            print('%d tries, %d cells, max Lakilester speed %.2f, %d hits [%.0fs]' % (tries, len(arch), top, len(hits), time.time() - t0), flush=True)
    pool.terminate()


if __name__ == '__main__':
    main()
