"""pra_01: where would a Lakilester speed boost carry Mario through the mirror (z = 0)?
Mario placed on the real side (z > 0), C-down; until the mount starts, Lakilester's moveSpeed is forced to S.
Records where Mario is once he is riding. Hit = Mario on the reflected side (z < 0) and in the room."""
import json, os, sys, multiprocessing as mp
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from pm import *
CD = 0x0400
W = {}


def init():
    from emu import Emu
    d = '/dev/shm/pmbot/ls%d' % os.getpid(); os.makedirs(d, exist_ok=True)
    W['e'], W['d'] = Emu(os.environ['PM_ROM'], d), d


def laki(e):
    for n in npcs(e):
        if n['id'] == -4: return n


def floor_y(x):
    return -60.0 if x < 610 else (-30.0 if x < 1000 else 0.0)


def run(x):
    e = W['e']
    out = []
    for z in [-220.0 + 4 * i for i in range(0, 111)]:
      for S in (8.0, 12.0, 16.0, 20.0, 25.0):
            e.load('states/pra01_start.st')
            e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, floor_y(x) + 5); e.wf32(PLAYER + PS_POS + 8, z)
            for i in range(25): e.step(0, 0, 0, 2)
            p0 = player(e)
            if abs(p0['x'] - x) > 1 or abs(p0['z'] - z) > 1 or tuple(where(e)[:2]) != (21, 0):
                break   # this z is not standable; the remaining S values for it are skipped
            e.step(CD, 0, 0, 2)
            mounted = False
            for f in range(40):
                p = player(e)
                if p['action'] != 33:
                    l = laki(e)
                    if l: e.wf32(l['addr'] + 0x18, float(S))
                e.step(0, 0, 0, 2)
                p = player(e)
                if p['action'] == 33 and e.s8(0x8010EBB0 + 3) != 0 if False else False:
                    pass
            p = player(e)
            if tuple(where(e)[:2]) != (21, 0) or e.s16(GAME_MODE) != GM_WORLD:
                continue
            out.append((x, z, S, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), p['action']))
    return out


if __name__ == '__main__':
    xs = [400.0 + 4 * i for i in range(0, 163)]
    pool = mp.get_context('spawn').Pool(4, initializer=init)
    res = [r for o in pool.map(run, xs) for r in o]
    json.dump(res, open(sys.argv[1], 'w'))
    hits = [r for r in res if (r[1] > 0) != (r[5] > 0) and r[6] == 33 and 400 < r[3] < 1050 and r[4] > -100]
    print(len(res), 'runs,', len(hits), 'end riding on the other side of the mirror')
    for h in hits[:30]: print(h)
    pool.terminate()
