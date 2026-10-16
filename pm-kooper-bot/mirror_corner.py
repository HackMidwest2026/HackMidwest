"""pra_02: Mario placed around the right pillar (x 740..800, z 13..70, 1-unit grid), Lakilester's speed forced to S
from the C-down press until the mount starts (S = 0 means left alone). Which spots put Mario behind the mirror?"""
import os, sys, json, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
CD = 0x0400
W = {}


def init():
    from emu import Emu
    d = '/dev/shm/pmbot/mc%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'] = Emu(os.environ['PM_ROM'], d)


def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n


def run(x):
    e = W['e']
    out = []
    for z in range(13, 71):
        for S in (0, 10, 25, 50):
            e.load('states/pra02_start.st')
            e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, float(z))
            for i in range(20): e.step(0, 0, 0, 2)
            p0 = player(e)
            if abs(p0['x'] - x) > 0.5 or abs(p0['z'] - z) > 0.5:
                break
            e.step(CD, 0, 0, 2)
            for i in range(30):
                if S and player(e)['action'] != 33:
                    l = laki(e)
                    if l: e.wf32(l['addr'] + 0x18, float(S))
                e.step(0, 0, 0, 2)
            p = player(e)
            if p['action'] == 33 and p['z'] < -1:
                out.append((x, z, S, round(p['x'], 1), round(p['z'], 1)))
    return out


if __name__ == '__main__':
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    res = [r for o in pool.map(run, list(range(740, 801))) for r in o]
    json.dump(res, open(sys.argv[1], 'w'))
    import collections
    print(len(res), 'crossings')
    for S in (0, 10, 25, 50):
        pts = sorted((r[0], r[1]) for r in res if r[2] == S)
        print('speed', S, ':', len(pts), 'spots; x range', (min(p[0] for p in pts), max(p[0] for p in pts)) if pts else None,
              'z range', (min(p[1] for p in pts), max(p[1] for p in pts)) if pts else None)
    print('sample', [r for r in res if r[2] == 0][:15])
    pool.terminate()
