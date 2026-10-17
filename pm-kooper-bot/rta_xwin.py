"""x tolerance of the 'hold up from step 3' funnel: place Mario at (X, Z0) on step 3 (or step 2), hold up 40 frames,
then neutral 6; report where he ends and whether it is in the usable corner. usage: rta_xwin.py Z0 [X0 X1 STEP]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rxwin')
def in_zone(x, z, y):
    return (abs(y + 20) < 0.5 and -145.5 <= z <= -72 and x >= 871.5 and x <= 871.5 + 0.175 * (-72 - z) and math.hypot(x - 530.8, z + 13) >= 370.4)
z0 = float(sys.argv[1]); x0, x1, st = (float(a) for a in sys.argv[2:5]) if len(sys.argv) > 4 else (874, 892, 0.25)
e.load('states/pra01_top_start.st'); e.step(0, 0, 0, 2); e.save('/dev/shm/pmbot/rxwin/b.st')
x = x0
while x <= x1 + 1e-6:
    e.load('/dev/shm/pmbot/rxwin/b.st'); e.step(0, 0, 0, 2)
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, -7.0); e.wf32(PLAYER + PS_POS + 8, z0)
    for i in range(15): e.step(0, 0, 0, 2)
    s = player(e)
    for i in range(40): e.step(0, *stick_for(270, 80), 2)
    for i in range(6): e.step(0, 0, 0, 2)
    p = player(e)
    print('x %.2f start y %.0f -> (%.2f, %.1f, %.2f) %s' % (x, s['y'], p['x'], p['y'], p['z'], 'ZONE' if in_zone(p['x'], p['z'], p['y']) and p['action'] == 0 else ''))
    x += st
