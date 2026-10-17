"""What-if: move the stale target and all fill points (history x < 570) K units further left in RAM, then run the simple corner
ending (W=2, D1=4, N=22, T=5: stand in the step-2 corner, then left + C-down) and report the best spike speed and
whether it clips. Tells how much further left the rock wiggle must be for the simple ending to work.
usage: rta_shift.py K [K ...]"""
import os, sys
from rta_end5 import *
for K in map(float, sys.argv[1:]):
    e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/shift%d' % os.getpid()) if 'e' not in dir() else e
    e.load('states/pra01_topright_rj.st'); e.step(0, 0, 0, 2)
    for i in range(40):
        if e.f32(HIST + 16 * i + 4) < 570: e.wf32(HIST + 16 * i + 4, e.f32(HIST + 16 * i + 4) - K)
    e.save('/dev/shm/pmbot/shift_start.st')
    os.environ['START'] = '/dev/shm/pmbot/shift_start.st'
    fr = run_base(e, 2, 4, 22, 5)
    for i in range(16): e.step(0, *U_, 2); fr += 1
    e.save('/dev/shm/pmbot/shift_b.st'); best = None
    for c in range(fr + 1, fr + 40):
        for P in (0, 1):
            e.load('/dev/shm/pmbot/shift_b.st'); g = fr
            while g < c - P: e.step(0, *U_, 2); g += 1
            for i in range(P): e.step(0, *SD['L'], 2)
            p = player(e); e.step(CD, *SD['L'], 2); spd = laki(e)['speed']
            if best is None or spd > best[0]: best = (spd, c, P, p['x'], p['z'])
    e.load('/dev/shm/pmbot/shift_b.st'); g = fr
    while g < best[1] - best[2]: e.step(0, *U_, 2); g += 1
    for i in range(best[2]): e.step(0, *SD['L'], 2)
    e.step(CD, *SD['L'], 2)
    for i in range(60): e.step(0, 0, 0, 2)
    print('K %.0f: best spike %.2f (frame %d, left %d frame(s) before + on C-down, Mario %.2f %.2f) -> %s' % (K, best[0], best[1], best[2], best[3], best[4], 'CLIP' if player(e)['z'] > 1 else 'no clip'))
