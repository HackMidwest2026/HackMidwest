"""pra_02 (first palace room) REVERSE mirror clip, forced-speed map: Mario placed BEHIND the mirror at (x, z),
C-down, Lakilester speed forced to S until the mount; hit = Mario riding in front of the mirror (z > 1).
x 0..1000 step 2, z -30..-12 step 1, S 20..160 step 20 (right end: x 940..1000 step 1, z -110..-12 step 2, S 100..260 step 10)."""
import os, sys, json, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
CD = 0x0400
W = {}
SPEEDS = list(range(100, 261, 10))


def init():
    from emu import Emu
    d = '/dev/shm/pmbot/rv%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'] = Emu(os.environ['PM_ROM'], d)


def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n


def floor_y(x):
    return 0.0


def run(x):
    e = W['e']
    out = []
    for k in range(0, 50):
        z = -110 + 2 * k
        for S in SPEEDS:
            e.load('states/pra02_start.st')
            e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, floor_y(x) + 3); e.wf32(PLAYER + PS_POS + 8, float(z))
            for i in range(20): e.step(0, 0, 0, 2)
            p0 = player(e)
            if abs(p0['x'] - x) > 0.5 or abs(p0['z'] - z) > 0.5 or tuple(where(e)[:2]) != (21, 1):
                break
            e.step(CD, 0, 0, 2)
            for i in range(30):
                if player(e)['action'] != 33:
                    l = laki(e)
                    if l: e.wf32(l['addr'] + 0x18, float(S))
                e.step(0, 0, 0, 2)
            if tuple(where(e)[:2]) != (21, 1): continue
            p = player(e)
            if p['action'] == 33 and p['z'] > 1 and 0 < p['x'] < 1000 and p['y'] > -100:
                out.append((x, z, S, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)))
    return out


if __name__ == '__main__':
    xs = list(range(940, 1001, 1))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    res = [r for o in pool.imap_unordered(run, xs, chunksize=2) for r in o]
    json.dump(res, open(sys.argv[1], 'w'))
    print(len(res), 'crossings')
    import collections
    for S in SPEEDS:
        pts = [r for r in res if r[2] == S]
        if pts: print('S', S, len(pts), 'x', min(r[0] for r in pts), max(r[0] for r in pts), 'z', min(r[1] for r in pts), max(r[1] for r in pts))
    pool.terminate()
