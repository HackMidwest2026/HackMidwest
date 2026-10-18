"""Full simple ending with a hammer at every 90-degree stick change (B pressed with the new direction already held,
then keep holding it): up 10, B+right, right R1, B+down, down D1, A + down N, B+left, left until the forced drop,
release during the drop (8), left T, B+up, hold up; final: flick to down (gap G neutral frames, then down P frames),
C-down with down held on frame c. Scans c and prints speeds / clips.
usage: rta_hammer2.py (env T, N, D1, R1, HU=1 hammer before up, HL=1 hammer before the left run)"""
import os, sys
from rta_end5 import *
B = 0x40
E = lambda k, d: int(os.environ.get(k, d))
def route(e, T, N, D1, R1, HU, HL, log=None):
    e.load(os.environ.get('START', 'states/pra01_topright_pa160.st')); e.step(0, 0, 0, 2)
    fr = [0]
    def st(b, s, tag=''):
        e.step(b, *s, 2); fr[0] += 1
        if log is not None: log(b, s, tag)
    def ham(s, name):   # B with the new direction held, keep holding it through the 10-frame swing
        st(B, s, 'hammer (B) with %s held' % name)
        for i in range(9): st(0, s, 'hammer swing, holding %s' % name)
    for i in range(10): st(0, U_, 'hold up')
    ham(SD['R'], 'right')
    for i in range(R1): st(0, SD['R'], 'hold right: very top-right corner')
    ham(SD['D'], 'down')
    for i in range(D1): st(0, SD['D'], 'hold down')
    for i in range(N): st(0x80 if i < 12 else 0, SD['D'], 'A + hold down: jump onto the top step, walk down')
    if HL: ham(SD['L'], 'left')
    else:
        for i in range(4): st(0, (0, 0), 'release')
    k = 0
    while player(e)['action'] != 9 and k < 80: st(0, SD['L'], 'hold left'); k += 1
    for i in range(8): st(0, (0, 0), 'release during the forced drop: always lands at x 911.9 on step 3')
    for i in range(T): st(0, SD['L'], 'left %d frames' % T)
    if HU: ham(U_, 'up')
    else:
        for i in range(2): st(0, (0, 0), 'release')
    return fr[0]
if __name__ == '__main__':
    T, N, D1, R1, HU, HL = E('T', 5), E('N', 22), E('D1', 4), E('R1', 10), E('HU', 1), E('HL', 1)
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rh2%d' % os.getpid())
    fr0 = route(e, T, N, D1, R1, HU, HL); e.save('/dev/shm/pmbot/rh2_b%d.st' % os.getpid())
    p = player(e); print('T %d N %d D1 %d R1 %d HU %d HL %d: after the route frame %d Mario (%.2f, %.2f, %.2f)' % (T, N, D1, R1, HU, HL, fr0, p['x'], p['y'], p['z']))
    hits = []
    for c in range(fr0 + 15, fr0 + 70):
        for G, P in ((0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (0, 3)):
            e.load('/dev/shm/pmbot/rh2_b%d.st' % os.getpid()); g = fr0
            while g < c - P - G: e.step(0, *U_, 2); g += 1
            for i in range(G): e.step(0, 0, 0, 2); g += 1
            for i in range(P): e.step(0, *SD['D'], 2); g += 1
            q = player(e); e.step(CD, *SD['D'], 2); spd = laki(e)['speed']
            if spd < 100: continue
            for i in range(60): e.step(0, 0, 0, 2)
            ok = player(e)['z'] > 1
            print(flush=True, *['  C-down frame %d gap %d down %d: speed %.2f Mario (%.2f, %.2f) %s' % (c, G, P, spd, q['x'], q['z'], 'CLIP' if ok else '-')])
