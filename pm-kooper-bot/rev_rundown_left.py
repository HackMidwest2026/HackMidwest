"""legend corner (states/pra01_topright.st): running jump down onto the top step (stick 80 deg, A at frame 4 held 8,
12 frames), wait W frames, then keep running down toward the mirror at angle D (tilt M); C-down tried on every frame
0..44 of that run. Hit = riding on the real side (z > 1). Prints hits and the best mount speeds with where Mario was.
usage: rev_rundown.py <out.json>"""
import json, os, sys, itertools, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/rd%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(task):
    Wt, D, M = task
    e = W['e']; base = os.path.join(W['d'], 'b.st')
    e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    s1 = stick_for(80, 80)
    for f in range(12): e.step(0x80 if 4 <= f < 12 else 0, *s1, 2)
    for f in range(Wt): e.step(0, 0, 0, 2)
    e.save(base)
    s = stick_for(D, M)
    hits, recs = [], []
    for f in range(70):
        e.load(base); e.step(0, 0, 0, 2)
        for i in range(f): e.step(0, *s, 2)
        p = player(e)
        e.step(CD, *s, 2)
        spd, last = None, 0
        for i in range(30):
            if spd is None and player(e)['action'] == 33: spd = last
            l = laki(e); last = l['speed'] if l else 0
            e.step(0, 0, 0, 2)
        q = player(e)
        rec = (Wt, D, M, f, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), round(spd or 0, 1), round(q['x'], 1), round(q['y'], 1), round(q['z'], 1))
        recs.append(rec)
        if q['action'] == 33 and q['z'] > 1 and tuple(where(e)[:2]) == (21, 0): hits.append(rec)
    return hits, recs
if __name__ == '__main__':
    tasks = list(itertools.product(range(40, 124, 4), (140, 150, 160, 170), (80,)))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    hits, recs = [], []
    for h, r in pool.imap_unordered(run, tasks, chunksize=2):
        hits += h; recs += r
        for x in h: print('HIT', x, flush=True)
    json.dump({'hits': hits, 'recs': recs}, open(sys.argv[1], 'w'))
    print(len(hits), 'hits of', len(recs), 'C-downs; best mount speeds:')
    for r in sorted(recs, key=lambda r: -r[7])[:10]: print(r)
    near = [r for r in recs if r[6] > -45]
    print('best with Mario near the mirror (z > -45):')
    for r in sorted(near, key=lambda r: -r[7])[:10]: print(r)
    pool.terminate()
