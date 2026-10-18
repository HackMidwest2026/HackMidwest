"""Hold-up ending (no flick): up 10, right 10 into the corner (no hammer: Laki is idle), B+down (hammer), down 4,
A + down 22, B+left, left until the forced drop, release during it (8), left T, release, stand until X, then hold up
continuously (Mario walks into the z -145 wall and slides down the riser into the step-2 corner) and press C-down
with up still held on frame c. Prints every clipping (T, X, c). usage: rta_holdup.py [T ...]"""
import os, sys
from multiprocessing import Pool
from rta_end5 import *
B = 0x40
def route(e, T, st):
    for i in range(10): st(0, U_, 'hold up')
    for i in range(10): st(0, SD['R'], 'hold right: very top-right corner')
    st(B, SD['D'], 'hammer (B) with down held')
    for i in range(9): st(0, SD['D'], 'hammer swing, holding down')
    for i in range(4): st(0, SD['D'], 'hold down')
    for i in range(22): st(0x80 if i < 12 else 0, SD['D'], 'A + hold down: jump onto the top step, walk down')
    st(B, SD['L'], 'hammer (B) with left held')
    for i in range(9): st(0, SD['L'], 'hammer swing, holding left')
    k = 0
    while player(e)['action'] != 9 and k < 80: st(0, SD['L'], 'hold left'); k += 1
    for i in range(8): st(0, (0, 0), 'release during the forced drop: always lands at x 911.9 on step 3')
    for i in range(T): st(0, SD['L'], 'left %d frames' % T)
    st(0, (0, 0), 'release, stand on step 3')
def job(T):
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rhu%d' % T)
    e.load(os.environ.get('START', 'states/pra01_topright_pa160.st')); e.step(0, 0, 0, 2)
    fr = [0]
    def st(b, s, tag=''):
        e.step(b, *s, 2); fr[0] += 1
    route(e, T, st); f0 = fr[0]; p0 = player(e)
    e.save('/dev/shm/pmbot/rhu%d/b.st' % T)
    out = ['T %d: stands at (%.2f, %.2f, %.2f) from frame %d' % (T, p0['x'], p0['y'], p0['z'], f0)]
    for X in range(f0, f0 + 50):
        for c in range(max(X + 1, 118), 142):
            e.load('/dev/shm/pmbot/rhu%d/b.st' % T); g = f0
            while g < X: e.step(0, 0, 0, 2); g += 1
            while g < c: e.step(0, *U_, 2); g += 1
            p = player(e); e.step(CD, *U_, 2); spd = laki(e)['speed']
            if spd < 115.5 or p['action'] not in (0, 1, 2): continue
            for i in range(60): e.step(0, 0, 0, 2)
            out.append('  up from frame %d, C-down frame %d: speed %.2f Mario (%.2f, %.2f, %.2f) act %d %s' % (X, c, spd, p['x'], p['y'], p['z'], p['action'], 'CLIP' if player(e)['z'] > 1 else '-'))
    return out
if __name__ == '__main__':
    Ts = [int(a) for a in sys.argv[1:]] or [3, 4, 5, 6]
    with Pool(4, maxtasksperchild=1) as p:
        for o in p.imap(job, Ts):
            print('\n'.join(o), flush=True)
