"""legend corner, ~1 s wait (states/pra01_topright_fast.st): running jump down onto the top step that flows straight
into a continuous run (no stop): stick angle D1 from the jump on for K frames, then angle D2 (tilt M) until frame
150; C-down tried on every frame from the landing on. Hit = riding on the real side (z > 1).
usage: rev_nostop.py <out.json>"""
import json, os, sys, itertools, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/ns%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(task):
    D1, K, D2, M = task
    e = W['e']; chk = os.path.join(W['d'], 'c.st')
    s1, s2 = stick_for(D1, 80), stick_for(D2, M)
    seq = [(0x80 if 4 <= f < 12 else 0, *(s1 if f < K else s2)) for f in range(150)]
    e.load('states/pra01_topright_fast.st'); e.step(0, 0, 0, 2)
    hits, recs = [], []
    for k, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        if k < 14 or k + 1 >= len(seq): continue
        p = player(e)
        e.save(chk)
        e.step(CD, *seq[k + 1][1:], 2)
        spd, last = None, 0
        for i in range(30):
            if spd is None and player(e)['action'] == 33: spd = last
            l = laki(e); last = l['speed'] if l else 0
            e.step(0, 0, 0, 2)
        q = player(e)
        rec = (D1, K, D2, M, k, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), round(spd or 0, 1), round(q['x'], 1), round(q['y'], 1), round(q['z'], 1))
        recs.append(rec)
        if q['action'] == 33 and q['z'] > 1 and tuple(where(e)[:2]) == (21, 0): hits.append(rec)
        e.load(chk)
    return hits, recs
if __name__ == '__main__':
    tasks = list(itertools.product((80, 90, 100), (12, 20, 30, 40), (90, 110, 130, 150, 170, 180, 200), (80, 40)))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    hits, recs = [], []
    for h, r in pool.imap_unordered(run, tasks, chunksize=2):
        hits += h; recs += r
        for x in h: print('HIT', x, flush=True)
    json.dump({'hits': hits, 'recs': recs}, open(sys.argv[1], 'w'))
    print(len(hits), 'hits of', len(recs), 'C-downs; best mount speeds:')
    for r in sorted(recs, key=lambda r: -r[8])[:8]: print(r)
    print('best with Mario near the mirror (z > -45):')
    for r in sorted([r for r in recs if r[7] > -45], key=lambda r: -r[8])[:8]: print(r)
    pool.terminate()
