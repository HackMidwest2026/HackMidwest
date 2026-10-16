"""pra_01: how far left can Mario get along the rock at each z? Place Mario at (560, z), hold left (also up-left/down-left), report min x."""
import os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rr')
for z in range(12, 101, 4):
    row = []
    for deg in (270, 300, 240):
        e.load('states/pra01_start.st')
        e.wf32(PLAYER + PS_POS, 560.0); e.wf32(PLAYER + PS_POS + 4, -57.0); e.wf32(PLAYER + PS_POS + 8, float(z))
        for i in range(10): e.step(0, 0, 0, 2)
        mn = (999, 0)
        sx, sy = stick_for(deg, 80)
        for i in range(60):
            e.step(0, sx, sy, 2)
            p = player(e)
            if p['x'] < mn[0]: mn = (round(p['x'], 2), round(p['z'], 1))
        row.append(mn)
    print(z, row)
