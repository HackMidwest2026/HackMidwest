"""Which speed / position combination is easiest for the reverse mirror clip (pra_01, from behind the mirror)?
Forced-speed map on a fine grid over the two regions that cross: near the mirror (x 680..830, z -45..-12) and the
stair strip (x 860..895, z -160..-70). Mario is dropped at (x, 10, z) from states/pra01_top_start.st; for each S in
90..300 step 5: C-down, Lakilester's speed forced to S until the mount; cross = riding on the real side (z > 1).
Output: {"x,z": [crossing speeds]}. usage: rev_easy.py <out.json> [region A|B]"""
import os, sys, json, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
CD = 0x0400
SPEEDS = list(range(90, 301, 5))
REG = sys.argv[2] if len(sys.argv) > 2 else 'A'
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/ez%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(x):
    e = W['e']; out = {}
    zs = range(-45, -11) if REG == 'A' else range(-160, -69, 2)
    for z in zs:
        e.load('states/pra01_top_start.st')
        e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, 10.0); e.wf32(PLAYER + PS_POS + 8, float(z))
        for i in range(20): e.step(0, 0, 0, 2)
        p0 = player(e)
        if abs(p0['x'] - x) > 0.5 or abs(p0['z'] - z) > 0.5 or tuple(where(e)[:2]) != (21, 0): continue
        base = os.path.join(W['d'], 'b.st'); e.save(base)
        ok = []
        for S in SPEEDS:
            e.load(base); e.step(0, 0, 0, 2)
            e.step(CD, 0, 0, 2)
            for i in range(30):
                if player(e)['action'] != 33:
                    l = laki(e)
                    if l: e.wf32(l['addr'] + 0x18, float(S))
                e.step(0, 0, 0, 2)
            p = player(e)
            if tuple(where(e)[:2]) == (21, 0) and p['action'] == 33 and p['z'] > 1: ok.append(S)
        out['%d,%d' % (x, z)] = {'y': round(p0['y'], 1), 'S': ok}
    return out
if __name__ == '__main__':
    xs = range(680, 831) if REG == 'A' else range(860, 896)
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    res = {}
    for o in pool.imap_unordered(run, xs, chunksize=2): res.update(o)
    json.dump(res, open(sys.argv[1], 'w'))
    hit = {k: v for k, v in res.items() if v['S']}
    print(len(res), 'standable spots,', len(hit), 'cross at some speed')
    pool.terminate()
