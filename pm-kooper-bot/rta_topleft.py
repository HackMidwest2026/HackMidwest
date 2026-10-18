"""Alternative ending: from the very top-right corner run LEFT along the top wall, then jump down over the stair rail
holding down, land on the stairs, and walk back up into the step-2 corner. Stage 1 (MODE=land): up 10, right 10,
B+left (hammer, left held), left k frames, release 1, down D0 (run-up, default 4), A + down held D frames, release; report where Mario lands.
usage: MODE=land rta_topleft.py"""
import itertools, os, sys
from multiprocessing import Pool
from rta_end5 import *
B = 0x40
def start(e):
    e.load(os.environ.get('START', 'states/pra01_topright_fast.st')); e.step(0, 0, 0, 2)
    for i in range(10): e.step(0, *U_, 2)
    for i in range(10): e.step(0, *SD['R'], 2)
    e.step(B, *SD['L'], 2)
    for i in range(9): e.step(0, *SD['L'], 2)
    return 20 + 10
def land(a):
    k, D = a
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rtl%d' % os.getpid())
    fr = start(e)
    for i in range(k): e.step(0, *SD['L'], 2)
    x0 = player(e)['x']
    e.step(0, 0, 0, 2)
    for i in range(int(os.environ.get('D0', 4))): e.step(0, *SD['D'], 2)
    for i in range(40):
        e.step(0x80 if i < 12 else 0, *(SD['D'] if i < D else (0, 0)), 2)
        if i > 3 and player(e)['action'] in (0, 1, 2): break
    for i in range(6): e.step(0, 0, 0, 2)
    p = player(e)
    return k, D, round(x0, 2), (round(p['x'], 2), round(p['y'], 2), round(p['z'], 2), p['action'])
if os.environ.get('MODE', 'land') == 'land' and __name__ == '__main__':
    with Pool(4, maxtasksperchild=1) as pool:
        for r in pool.imap(land, [(k, D) for k in map(int, os.environ.get('KS', '17-24').split('-')) for D in (30,)] if False else [(k, D) for k in range(int(os.environ.get('K0', 17)), int(os.environ.get('K1', 25))) for D in map(int, os.environ.get('DS', '0,4,8,10,12,14,16,20,30').split(','))], chunksize=1): print(r, flush=True)


def clipsearch(a):
    """MODE=search: k left frames, run-up D0, A + down D, release; stand until frame u (counted from the landing),
    then hold up to the end; C-down (up held) on each frame. Returns every clipping (u, c)."""
    k, D0, D = a
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rts%d' % os.getpid())
    w = '/dev/shm/pmbot/rts%d' % os.getpid()
    start(e); fr = 30
    for i in range(k): e.step(0, *SD['L'], 2); fr += 1
    e.step(0, 0, 0, 2); fr += 1
    for i in range(D0): e.step(0, *SD['D'], 2); fr += 1
    for i in range(40):
        e.step(0x80 if i < 12 else 0, *(SD['D'] if i < D else (0, 0)), 2); fr += 1
        if i > 3 and player(e)['action'] in (0, 1, 2): break
    land = fr; pl = player(e)
    e.save(w + '/l.st'); out = []; best = (0,)
    for u in range(0, 40):
        e.load(w + '/l.st')
        for i in range(u): e.step(0, 0, 0, 2)
        for j in range(45):
            e.save(w + '/c.st'); p = player(e)
            e.step(CD, *U_, 2); spd = laki(e)['speed']
            if p['action'] in (0, 1, 2) and spd > best[0]: best = (round(spd, 2), u, j, round(p['x'], 2), round(p['z'], 2))
            if spd >= 115.5 and p['action'] in (0, 1, 2):
                for i in range(60): e.step(0, 0, 0, 2)
                if player(e)['z'] > 1: out.append((u, j, round(spd, 2), round(p['x'], 2), round(p['z'], 2)))
            try:
                e.load(w + '/c.st')
            except RuntimeError:   # rare bad savestate: rebuild this frame by replaying from the landing state
                e.load(w + '/l.st')
                for i in range(u): e.step(0, 0, 0, 2)
                for i in range(j): e.step(0, *U_, 2)
            e.step(0, *U_, 2)
    return a, land, (round(pl['x'], 2), round(pl['y'], 2), round(pl['z'], 2)), (out, best)


if os.environ.get('MODE') == 'search' and __name__ == '__main__':
    args = [tuple(map(int, a.split(','))) for a in os.environ['ARGS'].split()] if os.environ.get('ARGS') else [(k, D0, D) for k in range(20, 24) for D0 in (3, 4, 6) for D in (8, 12, 16)]
    with Pool(4, maxtasksperchild=1) as pool:
        for a, land, pl, out in pool.imap(clipsearch, args, chunksize=1):
            print('k %d run-up %d A+down %d: lands frame %d at %s; clips (up after u frames, C-down j frames after the up press):' % (*a, land, pl), out or '-', flush=True)
