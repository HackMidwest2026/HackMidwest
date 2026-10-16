"""pra_01 reflected side, forced-speed map over the upper area where Lakilester gets fast: x 740..1000 step 4,
z -214..-79 step 3, S 60..140 step 5. Mario placed at (x, z), C-down, speed forced to S until the mount;
hit = riding on the real side (z > 1)."""
import os, sys, json, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
CD = 0x0400
W = {}
SPEEDS = list(range(60, 141, 5))


def init():
    from emu import Emu
    d = '/dev/shm/pmbot/rv%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'] = Emu(os.environ['PM_ROM'], d)


def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n


def floor_y(x):
    return -60.0 if x < 610 else (-30.0 if x < 1000 else 0.0)


def run(x):
    e = W['e']
    out = []
    for k in range(0, 46):
        z = -214 + 3 * k
        for S in SPEEDS:
            e.load('states/pra01_top_start.st')
            e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, 10.0); e.wf32(PLAYER + PS_POS + 8, float(z))
            for i in range(20): e.step(0, 0, 0, 2)
            p0 = player(e)
            if abs(p0['x'] - x) > 0.5 or abs(p0['z'] - z) > 0.5 or tuple(where(e)[:2]) != (21, 0):
                break
            e.step(CD, 0, 0, 2)
            for i in range(30):
                if player(e)['action'] != 33:
                    l = laki(e)
                    if l: e.wf32(l['addr'] + 0x18, float(S))
                e.step(0, 0, 0, 2)
            if tuple(where(e)[:2]) != (21, 0): continue
            p = player(e)
            if p['action'] == 33 and p['z'] > 1 and 400 < p['x'] < 1050 and p['y'] > -100:
                out.append((x, z, S, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)))
    return out


if __name__ == '__main__':
    xs = list(range(740, 1001, 4))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    res = [r for o in pool.imap_unordered(run, xs, chunksize=2) for r in o]
    json.dump(res, open(sys.argv[1], 'w'))
    print(len(res), 'crossings')
    import collections
    for S in SPEEDS:
        pts = [r for r in res if r[2] == S]
        if pts: print('S', S, len(pts), 'x', min(r[0] for r in pts), max(r[0] for r in pts), 'z', min(r[1] for r in pts), max(r[1] for r in pts))
    pool.terminate()
