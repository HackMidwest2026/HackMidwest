"""pra_01 (outside the palace): with Lakilester's speed forced to S at C-down, which standable spots near the places
where walls meet the mirror put Mario on the OTHER side of the mirror? 1-unit grid; regions: left end (rock walls,
x 470..560) and right end (stairs/palace front, x 800..1000); z -80..80 both sides; S = 30, 50, 70, 90, 120."""
import os, sys, json, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
CD = 0x0400
W = {}
SPEEDS = (30, 50, 70, 90, 120)


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
    for z in range(-80, 81):
        if abs(z) < 12: continue
        st = 'states/pra01_start.st' if z > 0 else 'states/pra01_top_start.st'
        for S in SPEEDS:
            e.load(st)
            e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, floor_y(x) + 3); e.wf32(PLAYER + PS_POS + 8, float(z))
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
            if p['action'] == 33 and (p['z'] > 0) != (z > 0) and abs(p['z']) > 1 and 400 < p['x'] < 1050 and p['y'] > -100:
                out.append((x, z, S, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)))
    return out


if __name__ == '__main__':
    xs = list(range(470, 561)) + list(range(800, 1001))
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    res = [r for o in pool.imap_unordered(run, xs, chunksize=2) for r in o]
    json.dump(res, open(sys.argv[1], 'w'))
    print(len(res), 'crossings')
    import collections
    for S in SPEEDS:
        pts = [r for r in res if r[2] == S]
        print('S', S, len(pts), 'from real side:', len([r for r in pts if r[1] > 0]), 'from reflected side:', len([r for r in pts if r[1] < 0]))
    for r in res[:40]: print(r)
    pool.terminate()
