"""pra_01 reverse mirror clip, final approach from the legend corner (states/pra01_topright.st).
Grid: run left L frames along the top corridor (Lakilester is released once Mario is 40+ away), stand W frames,
then run at angle D (stick 80 or 40) and press C-down on frame f of that run (0..35). Hit = Mario riding on the
real side (z > 1). The forced-speed map says the crossing strip is x 872..884, z -145..-79 at speed >= 120.
usage: rev_strip.py <out.json>"""
import json, os, sys, itertools, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/st%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(task):
    L, Wt, D, mag = task
    e = W['e']; base = os.path.join(W['d'], 'b.st')
    e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    lx, ly = stick_for(180, 80)
    for i in range(L): e.step(0, lx, ly, 2)
    for i in range(Wt): e.step(0, 0, 0, 2)
    e.save(base)
    sx, sy = stick_for(D, mag)
    hits, near = [], []
    for f in range(36):
        e.load(base); e.step(0, 0, 0, 2)
        for i in range(f): e.step(0, sx, sy, 2)
        p0 = player(e)
        e.step(CD, sx, sy, 2)
        spd = None
        for i in range(30):
            if spd is None and player(e)['action'] == 33: spd = last
            l = laki(e); last = l['speed'] if l else 0
            e.step(0, 0, 0, 2)
        p = player(e)
        rec = (L, Wt, D, mag, f, round(p0['x'], 1), round(p0['z'], 1), round(spd or 0, 1), round(p['x'], 1), round(p['y'], 1), round(p['z'], 1))
        if p['action'] == 33 and p['z'] > 1 and tuple(where(e)[:2]) == (21, 0): hits.append(rec)
        if 860 < p0['x'] < 895 and -150 < p0['z'] < -75: near.append(rec)
    return hits, near
if __name__ == '__main__':
    tasks = list(itertools.product(range(4, 34, 3), (0, 3, 6, 10, 15), (90, 100, 110, 120, 135, 150), (80, 40)))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    hits, near = [], []
    for h, n in pool.imap_unordered(run, tasks, chunksize=2):
        hits += h; near += n
        for x in h: print('HIT', x, flush=True)
    json.dump({'hits': hits, 'near': near}, open(sys.argv[1], 'w'))
    print(len(hits), 'hits;', len(near), 'C-downs from inside the strip; best strip speeds:')
    for r in sorted(near, key=lambda r: -r[7])[:15]: print(r)
    pool.terminate()
