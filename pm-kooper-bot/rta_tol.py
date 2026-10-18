"""Tolerance of each input in the one-run hold-up ending, with the two cued inputs placed by their cues: the stopping
B+up on the HS-th frame after the frame Mario lands on step 3 (y -10; base 4), and the C-down scanned 0..6 frames after
the frame he lands on step 2 (y -20); prints which offsets clip. Varies one input at a time around the base (R 10 right frames into the corner, D 4 down frames after the
corner hammer, A held 12 frames, N 31 frames of A + down before B+left) and prints which values clip.
usage: rta_tol.py"""
import os, sys
from multiprocessing import Pool
from rta_end5 import *
B = 0x40
def run(a):
    R, D, AH, N, HS = a
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rtol%d' % os.getpid())
    e.load(os.environ.get('START', 'states/pra01_topright_pa160.st')); e.step(0, 0, 0, 2)
    for i in range(10): e.step(0, *U_, 2)
    for i in range(R): e.step(0, *SD['R'], 2)
    e.step(B, *SD['D'], 2)
    for i in range(9 + D): e.step(0, *SD['D'], 2)
    for i in range(N): e.step(0x80 if i < AH else 0, *SD['D'], 2)
    e.step(B, *SD['L'], 2)
    k = 0
    while not (abs(player(e)['y'] + 10) < 0.01) and k < 80: e.step(0, *SD['L'], 2); k += 1
    for i in range(HS - 1): e.step(0, *SD['L'], 2)
    e.step(B, *U_, 2)
    k = 0
    while not (abs(player(e)['y'] + 20) < 0.01) and k < 80: e.step(0, *U_, 2); k += 1
    q = player(e)
    w = '/dev/shm/pmbot/rtol%d/l.st' % os.getpid(); e.save(w)
    best, offs = 0, []
    for off in range(0, 7):
        e.load(w)
        for i in range(off): e.step(0, *U_, 2)
        e.step(CD, *U_, 2); spd = laki(e)['speed']; best = max(best, spd)
        if spd < 100: continue
        for i in range(60): e.step(0, 0, 0, 2)
        if player(e)['z'] > 1: offs.append(off)
    return a, best, (q['x'], q['z']), offs
if __name__ == '__main__':
    base = dict(R=10, D=4, AH=12, N=31, HS=4)
    cases = []
    for k, vals in (('R', range(4, 31, 2)), ('D', range(0, 11)), ('AH', range(4, 31, 2)), ('N', range(28, 36)), ('HS', range(2, 7))):
        for v in vals:
            d = dict(base); d[k] = v; cases.append((k, (d['R'], d['D'], d['AH'], d['N'], d['HS'])))
    with Pool(4, maxtasksperchild=1) as p:
        res = p.map(run, [c[1] for c in cases], chunksize=1)
    cur = None
    for (k, a), (_, spd, q, offs) in zip(cases, res):
        if k != cur: print('== vary %s (others at base %s)' % (k, base)); cur = k
        print('  %s=%-3d best speed %6.2f  Mario lands at (%.2f, %.2f)  clips with C-down %s frames after the landing' % (k, a[('R', 'D', 'AH', 'N', 'HS').index(k)], spd, q[0], q[1], offs or '-'))
