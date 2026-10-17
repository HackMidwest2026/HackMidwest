"""With the stale target and fill points moved K units left (RAM what-if), count which simple endings clip:
T (left frames after the step-3 landing: 5 -> corner 884.35, 6 -> 880.5), P frames of left before C-down (C-down frame
also holds left), C-down frame c. usage: rta_shift_win.py K"""
import os, sys
from rta_end5 import *
K = float(sys.argv[1])
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/shw%d' % os.getpid())
e.load('states/pra01_topright_rj.st'); e.step(0, 0, 0, 2)
for i in range(40):
    if e.f32(HIST + 16 * i + 4) < 570: e.wf32(HIST + 16 * i + 4, e.f32(HIST + 16 * i + 4) - K)
e.save('/dev/shm/pmbot/shw_start.st'); os.environ['START'] = '/dev/shm/pmbot/shw_start.st'
for T in (5, 6):
    for D in 'LD':
        fr = run_base(e, 2, 4, 22, T)
        for i in range(16): e.step(0, *U_, 2); fr += 1
        e.save('/dev/shm/pmbot/shw_b.st'); f0 = fr
        for P in (0, 1, 2, 3):
            row = []
            for c in range(112, 130):
                e.load('/dev/shm/pmbot/shw_b.st'); g = f0
                while g < c - P: e.step(0, *U_, 2); g += 1
                for i in range(P): e.step(0, *SD[D], 2)
                e.step(CD, *SD[D], 2); spd = laki(e)['speed']
                if spd < 100: row.append('.'); continue
                for i in range(60): e.step(0, 0, 0, 2)
                row.append('Y' if player(e)['z'] > 1 else 'n')
            print('K %g T %d dir %s P %d  C-down frames 112..129: %s' % (K, T, D, P, ''.join(row)))
