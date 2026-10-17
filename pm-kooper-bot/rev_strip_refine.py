"""Local refinement of the best rev_jumpdown4 runs (START = rock-jump top-right state): keep each run's route
(jump down D1 / A at J / N1 frames, then D2 for K frames), then replace the last part with random small stick
moves (biased to end at the strip's up-right corner, x ~884, z ~-144, moving down-left toward the rock) from frame
T0 on; C-down tried on every frame from T0 while Mario is in the strip. Hit = riding on the real side.
usage: rev_strip_refine.py <seed_results.json> <out.json> <minutes>"""
import json, os, random, sys, time, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
START = os.environ.get('START', 'states/pra01_topright_rj.st')
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/rf%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def prefix(D1, J, N1, D2, K, OSC, MAG, upto):
    s1, s2 = stick_for(D1, 80), stick_for(D2, 80)
    a, b = stick_for(330, MAG), stick_for(150, MAG)
    seq = [(0x80 if J <= f < J + 8 else 0, *s1) for f in range(N1)] + [(0, *s2)] * K + [(0, *(a if (i // OSC) % 2 == 0 else b)) for i in range(160)]
    return seq[:upto]
def run(task):
    pre, tail = task
    e = W['e']; chk = os.path.join(W['d'], 'c.st')
    e.load(START); e.step(0, 0, 0, 2)
    for b, sx, sy in pre: e.step(b, sx, sy, 2)
    best, hits = (0, None), []
    for k, (b, sx, sy) in enumerate(tail):
        e.step(b, sx, sy, 2)
        p = player(e)
        if 872 <= p['x'] <= 884 and -144 <= p['z'] <= -72 and p['action'] in (0, 1, 2):
            e.save(chk)
            nx = tail[k + 1] if k + 1 < len(tail) else (0, 0, 0)
            e.step(CD, nx[1], nx[2], 2)
            spd, last = None, 0
            for i in range(30):
                if spd is None and player(e)['action'] == 33: spd = last
                l = laki(e); last = l['speed'] if l else 0
                e.step(0, 0, 0, 2)
            q = player(e)
            if spd and spd > best[0]: best = (spd, k, (round(p['x'], 1), round(p['z'], 1)))
            if q['action'] == 33 and q['z'] > 1 and tuple(where(e)[:2]) == (21, 0):
                hits.append({'k': k, 'speed': spd, 'mario': (p['x'], p['y'], p['z']), 'end': (q['x'], q['y'], q['z'])})
            e.load(chk)
    return task, best, hits
def rand_tail(n):
    out = []
    while len(out) < n:
        r = random.random()
        if r < 0.2: st = (0, 0)
        elif r < 0.55: st = stick_for(random.uniform(300, 360), random.choice((15, 20, 30, 40)))   # up-right, away from the rock
        else: st = stick_for(random.uniform(130, 200), random.choice((15, 20, 30, 40)))           # down-left, toward the rock
        out += [(0, *st)] * random.choice((1, 1, 2, 3))
    return out[:n]
if __name__ == '__main__':
    seeds = json.load(open(sys.argv[1]))['near']
    seeds = sorted(seeds, key=lambda r: -r[12])[:30]
    out, minutes = sys.argv[2], float(sys.argv[3])
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    t0, top, hits, n = time.time(), (0, None), [], 0
    while time.time() - t0 < minutes * 60:
        tasks = []
        for _ in range(64):
            r = random.choice(seeds)
            D1, J, N1, D2, mag, K, OSC, MAG, kk = r[:9]
            T0 = max(N1 + K, kk - random.choice((6, 10, 15, 20, 30)))
            tasks.append((prefix(D1, J, N1, D2, K, OSC, MAG, T0), rand_tail(kk + 12 - T0)))
        for task, best, h in pool.map(run, tasks, chunksize=4):
            n += 1
            if best[0] > top[0]:
                top = (best[0], best[2]); json.dump({'speed': best[0], 'k': best[1], 'pre': task[0], 'tail': task[1]}, open(out, 'w'))
            for x in h:
                x['pre'], x['tail'] = task; hits.append(x)
                print('HIT', json.dumps({k: x[k] for k in ('k', 'speed', 'mario', 'end')}), flush=True)
                json.dump(hits, open(out.replace('.json', '_hits.json'), 'w'))
        print('%d tries, best mount speed in the strip %.1f at %s, %d hits [%.0fs]' % (n, top[0], top[1], len(hits), time.time() - t0), flush=True)
    pool.terminate()
