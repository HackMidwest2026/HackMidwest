"""pra_01 reverse mirror clip from the legend corner (states/pra01_topright.st): run down with a jump onto the stairs,
then steer into the crossing strip (x 872..884, z -145..-79). Grid: first stick angle D1 for N1 frames (A pressed
at frame J, held 8), then angle D2 at full or half tilt; C-down tried on every frame where Mario is within the
widened strip (x 860..895, z -155..-70). Prints hits and the best mount speeds seen in the strip.
usage: rev_jumpdown.py <out.json>"""
import json, os, sys, itertools, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
from corner_sweep import stick_for
CD = 0x0400
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/jd%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(task):
    D1, J, N1, D2, mag = task
    e = W['e']; chk = os.path.join(W['d'], 'c.st')
    seq = []
    s1 = stick_for(D1, 80); s2 = stick_for(D2, mag)
    for f in range(N1): seq.append((0x80 if J <= f < J + 8 else 0, *s1))
    seq += [(0, *s2)] * 40 + [(0, 0, 0)] * 20
    e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    hits, near = [], []
    for k, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        p = player(e)
        if 860 < p['x'] < 895 and -155 < p['z'] < -70 and p['action'] in (0, 1, 2):
            e.save(chk)
            e.step(CD, *seq[min(k + 1, len(seq) - 1)][1:], 2)
            spd, last = None, 0
            for i in range(30):
                if spd is None and player(e)['action'] == 33: spd = last
                l = laki(e); last = l['speed'] if l else 0
                e.step(0, 0, 0, 2)
            q = player(e)
            rec = (D1, J, N1, D2, mag, k, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), round(spd or 0, 1), round(q['x'], 1), round(q['y'], 1), round(q['z'], 1))
            near.append(rec)
            if q['action'] == 33 and q['z'] > 1 and tuple(where(e)[:2]) == (21, 0): hits.append(rec)
            e.load(chk)
    return hits, near
if __name__ == '__main__':
    tasks = list(itertools.product((90, 100, 110, 120, 135), (0, 2, 4, 6), (10, 14, 18, 22, 26), (120, 135, 150, 165, 180, 100), (80, 40)))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    hits, near = [], []
    for h, n in pool.imap_unordered(run, tasks, chunksize=4):
        hits += h; near += n
        for x in h: print('HIT', x, flush=True)
    json.dump({'hits': hits, 'near': near}, open(sys.argv[1], 'w'))
    print(len(hits), 'hits;', len(near), 'C-downs in the strip; best mount speeds there:')
    for r in sorted(near, key=lambda r: -r[9])[:15]: print(r)
    pool.terminate()
