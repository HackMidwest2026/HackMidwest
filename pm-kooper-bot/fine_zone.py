"""Exact standing range for a reverse-mirror-clip zone: forced-speed C-down test with Mario placed at (x, Y0, z) on
a fine grid (x step 0.25, z step 1) for each speed in SPEEDS. Hit = riding on the front side (z > 1), same map.
usage: fine_zone.py <state> <map_id> <x0> <x1> <z0> <z1> <speeds comma> <out.json>"""
import os, sys, json, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
CD = 0x0400
ST, MAPID = sys.argv[1], int(sys.argv[2])
X0, X1, Z0, Z1 = map(float, sys.argv[3:7]); SPEEDS = [float(s) for s in sys.argv[7].split(',')]
W = {}
def init():
    from emu import Emu
    d = '/dev/shm/pmbot/fz%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d
def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n
def run(x):
    e = W['e']; out = {}
    z = Z0
    while z <= Z1 + 1e-6:
        e.load(ST)
        e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, 10.0); e.wf32(PLAYER + PS_POS + 8, float(z))
        for i in range(20): e.step(0, 0, 0, 2)
        p0 = player(e)
        if abs(p0['x'] - x) < 0.05 and abs(p0['z'] - z) < 0.05 and tuple(where(e)[:2]) == (21, MAPID):
            base = os.path.join(W['d'], 'b.st'); e.save(base)
            ok = []
            for S in SPEEDS:
                e.load(base); e.step(0, 0, 0, 2); e.step(CD, 0, 0, 2)
                for i in range(30):
                    if player(e)['action'] != 33:
                        l = laki(e)
                        if l: e.wf32(l['addr'] + 0x18, S)
                    e.step(0, 0, 0, 2)
                p = player(e)
                if tuple(where(e)[:2]) == (21, MAPID) and p['action'] == 33 and p['z'] > 1: ok.append(S)
            out['%.2f,%.0f' % (x, z)] = {'y': round(p0['y'], 2), 'S': ok}
        z += 1.0
    return out
if __name__ == '__main__':
    xs = [round(X0 + 0.25 * i, 2) for i in range(int((X1 - X0) / 0.25) + 1)]
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    res = {}
    for o in pool.imap_unordered(run, xs, chunksize=2): res.update(o)
    json.dump(res, open(sys.argv[8], 'w'))
    for S in SPEEDS:
        pts = [tuple(map(float, k.split(','))) for k, v in res.items() if S in v['S']]
        if pts:
            print('speed %g: %d spots, x %.2f..%.2f, z %.0f..%.0f' % (S, len(pts), min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)))
        else:
            print('speed %g: none' % S)
    print('standable spots tested:', len(res))
    pool.terminate()
