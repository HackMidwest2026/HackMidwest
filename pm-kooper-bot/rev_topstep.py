"""legend corner (states/pra01_topright.st): running jump down (stick angle D, A at frame J held 8, N frames) onto the
top step by the palace doors, then stand still up to 200 frames while Lakilester flies to his stale target and races
back; C-down tried on every frame. Hit = riding on the real side (z > 1). Prints the best mount speeds.
usage: rev_topstep.py <out.json>"""
import json, os, sys, itertools, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/ts%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(task):
    D, J, N = task
    e = W['e']; chk = os.path.join(W['d'], 'c.st')
    s = stick_for(D, 80)
    seq = [(0x80 if J <= f < J + 8 else 0, *s) for f in range(N)] + [(0, 0, 0)] * 200
    e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    hits, recs = [], []
    for k, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        if k < N: continue
        p = player(e)
        e.save(chk)
        e.step(CD, 0, 0, 2)
        spd, last = None, 0
        for i in range(30):
            if spd is None and player(e)['action'] == 33: spd = last
            l = laki(e); last = l['speed'] if l else 0
            e.step(0, 0, 0, 2)
        q = player(e)
        rec = (D, J, N, k, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), round(spd or 0, 1), round(q['x'], 1), round(q['y'], 1), round(q['z'], 1))
        recs.append(rec)
        if q['action'] == 33 and q['z'] > 1 and tuple(where(e)[:2]) == (21, 0): hits.append(rec)
        e.load(chk)
    return hits, recs
if __name__ == '__main__':
    tasks = list(itertools.product((80, 90, 100, 110, 120), (2, 4, 6), (12, 14, 16, 20, 24)))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    hits, recs = [], []
    for h, r in pool.imap_unordered(run, tasks, chunksize=2):
        hits += h; recs += r
        for x in h: print('HIT', x, flush=True)
    json.dump({'hits': hits, 'recs': recs}, open(sys.argv[1], 'w'))
    print(len(hits), 'hits of', len(recs), 'C-downs; best mount speeds:')
    for r in sorted(recs, key=lambda r: -r[7])[:12]: print(r)
    pool.terminate()
