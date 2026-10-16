"""pra_01 reverse mirror clip, legend corner: run left along the top corridor L frames (to x ~ 870..890), wait W
frames while the released Lakilester flies toward his stale target and comes back fast, then jump down (stick angle
D, A at the first frame held 8) onto the stairs; C-down tried on every frame 0..40 after the jump starts.
Hit = riding on the real side (z > 1). Records mount speed and Mario's position at each C-down.
usage: rev_linger.py <out.json>"""
import json, os, sys, itertools, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/lg%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(task):
    L, Wt, D = task
    e = W['e']; base = os.path.join(W['d'], 'b.st')
    e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    for i in range(L): e.step(0, *stick_for(180, 80), 2)
    for i in range(Wt): e.step(0, 0, 0, 2)
    e.save(base)
    sx, sy = stick_for(D, 80)
    hits, recs = [], []
    for f in range(41):
        e.load(base); e.step(0, 0, 0, 2)
        for i in range(f): e.step(0x80 if i < 8 else 0, sx, sy, 2)
        p0 = player(e)
        e.step(CD | (0x80 if f < 8 else 0), sx, sy, 2)
        spd, last = None, 0
        for i in range(30):
            if spd is None and player(e)['action'] == 33: spd = last
            l = laki(e); last = l['speed'] if l else 0
            e.step(0, 0, 0, 2)
        q = player(e)
        rec = (L, Wt, D, f, round(p0['x'], 1), round(p0['y'], 1), round(p0['z'], 1), round(spd or 0, 1), round(q['x'], 1), round(q['y'], 1), round(q['z'], 1))
        recs.append(rec)
        if q['action'] == 33 and q['z'] > 1 and tuple(where(e)[:2]) == (21, 0): hits.append(rec)
    return hits, recs
if __name__ == '__main__':
    tasks = list(itertools.product((20, 22, 24, 26, 28), range(0, 64, 3), (90, 80, 100)))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    hits, recs = [], []
    for h, r in pool.imap_unordered(run, tasks, chunksize=2):
        hits += h; recs += r
        for x in h: print('HIT', x, flush=True)
    json.dump({'hits': hits, 'recs': recs}, open(sys.argv[1], 'w'))
    strip = [r for r in recs if 865 < r[4] < 892 and -152 < r[6] < -72]
    print(len(hits), 'hits;', len(strip), 'C-downs inside the strip; best speeds there:')
    for r in sorted(strip, key=lambda r: -r[7])[:12]: print(r)
    print('best speeds anywhere:')
    for r in sorted(recs, key=lambda r: -r[7])[:8]: print(r)
    pool.terminate()
