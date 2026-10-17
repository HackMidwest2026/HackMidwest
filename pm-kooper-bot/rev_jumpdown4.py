"""v4 (rev_jumpdown4.py): instead of standing, Mario steps back and forth inside the strip (OSC frames up-right at
tilt MAG, OSC frames down-left), so that at Lakilester's spike Mario's newest history point is farther from
Lakilester than Mario is (the follow formula then adds d/16). C-down tried on every frame in the strip.
v2: after the second run segment (K frames) Mario stands still 140 frames in/near the strip while Lakilester
flies to his stale target and races back; C-down tried on every frame in the strip.
pra_01 reverse mirror clip from the legend corner (states/pra01_topright.st): run down with a jump onto the stairs,
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
    D1, J, N1, D2, mag, K, OSC, MAG = task
    e = W['e']; chk = os.path.join(W['d'], 'c.st')
    seq = []
    s1 = stick_for(D1, 80); s2 = stick_for(D2, mag)
    for f in range(N1): seq.append((0x80 if J <= f < J + 8 else 0, *s1))
    a, b = stick_for(330, MAG), stick_for(150, MAG)
    seq += [(0, *s2)] * K + [(0, *(a if (i // OSC) % 2 == 0 else b)) for i in range(160)]
    e.load(os.environ.get('START', 'states/pra01_topright.st')); e.step(0, 0, 0, 2)
    hits, near = [], []
    for k, (b, sx, sy) in enumerate(seq):
        e.step(b, sx, sy, 2)
        p = player(e)
        if 870 < p['x'] < 886 and -150 < p['z'] < -70 and p['action'] in (0, 1, 2):
            e.save(chk)
            e.step(CD, *seq[min(k + 1, len(seq) - 1)][1:], 2)
            spd, last = None, 0
            for i in range(30):
                if spd is None and player(e)['action'] == 33: spd = last
                l = laki(e); last = l['speed'] if l else 0
                e.step(0, 0, 0, 2)
            q = player(e)
            rec = (D1, J, N1, D2, mag, K, OSC, MAG, k, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), round(spd or 0, 1), round(q['x'], 1), round(q['y'], 1), round(q['z'], 1))
            near.append(rec)
            if q['action'] == 33 and q['z'] > 1 and tuple(where(e)[:2]) == (21, 0): hits.append(rec)
            e.load(chk)
    return hits, near
if __name__ == '__main__':
    tasks = list(itertools.product((110, 120, 135), (4, 6), (14, 18), (150, 165, 180), (80,), (4, 8, 12, 16), (2, 3, 5), (20, 30)))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    hits, near = [], []
    for h, n in pool.imap_unordered(run, tasks, chunksize=4):
        hits += h; near += n
        for x in h: print('HIT', x, flush=True)
    json.dump({'hits': hits, 'near': near}, open(sys.argv[1], 'w'))
    print(len(hits), 'hits;', len(near), 'C-downs in the strip; best mount speeds there:')
    for r in sorted(near, key=lambda r: -r[12])[:15]: print(r)
    pool.terminate()
