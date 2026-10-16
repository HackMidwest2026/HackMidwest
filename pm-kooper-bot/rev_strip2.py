"""pra_01 reverse mirror clip from the legend corner (states/pra01_topright.st): route into the crossing strip
(x 872..884, z -145..-79, needs speed >= 120). Grid: left L frames along the corridor, down Dn frames, right R
frames, then stand; C-down tried on every frame from the start of the right run to 40 frames after.
Hit = riding on the real side (z > 1). Also records the speed at the mount for C-downs made inside the strip.
usage: rev_strip2.py <out.json>"""
import json, os, sys, itertools, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/s2%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(task):
    L, Dn, R, mag = task
    e = W['e']; base = os.path.join(W['d'], 'b.st')
    e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    for i in range(L): e.step(0, *stick_for(180, 80), 2)
    for i in range(Dn): e.step(0, *stick_for(90, 80), 2)
    e.save(base)
    tail = [stick_for(0, mag)] * R + [(0, 0)] * 40
    hits, near = [], []
    for f in range(len(tail)):
        e.load(base); e.step(0, 0, 0, 2)
        for i in range(f): e.step(0, *tail[i], 2)
        p0 = player(e)
        e.step(CD, *tail[f], 2)
        spd, last = None, 0
        for i in range(30):
            if spd is None and player(e)['action'] == 33: spd = last
            l = laki(e); last = l['speed'] if l else 0
            e.step(0, 0, 0, 2)
        p = player(e)
        rec = (L, Dn, R, mag, f, round(p0['x'], 1), round(p0['z'], 1), round(spd or 0, 1), round(p['x'], 1), round(p['y'], 1), round(p['z'], 1))
        if p['action'] == 33 and p['z'] > 1 and tuple(where(e)[:2]) == (21, 0): hits.append(rec)
        if 868 < p0['x'] < 888 and -150 < p0['z'] < -75: near.append(rec)
    return hits, near
if __name__ == '__main__':
    tasks = list(itertools.product(range(34, 46, 2), range(10, 34, 3), range(10, 22, 2), (80,)))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    hits, near = [], []
    for h, n in pool.imap_unordered(run, tasks, chunksize=2):
        hits += h; near += n
        for x in h: print('HIT', x, flush=True)
    json.dump({'hits': hits, 'near': near}, open(sys.argv[1], 'w'))
    print(len(hits), 'hits;', len(near), 'C-downs from inside the strip; best strip speeds:')
    for r in sorted(near, key=lambda r: -r[7])[:15]: print(r)
    pool.terminate()
