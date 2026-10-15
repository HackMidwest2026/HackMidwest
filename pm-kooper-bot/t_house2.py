"""walk into the corner until step-up, then a list of (buttons, deg, frames) segments; log every frame."""
import os, sys, json
from emu import Emu
from pm import *
from corner_sweep import stick_for
A, Z = 0x0080, 0x0020
e = Emu(os.environ.get('PM_ROM', 'pm-jp.z64'), '/dev/shm/pmbot/house2')
e.load('states/mac02_start.st'); e.step(0, 0, 0, 2)
x0, z0, deg0 = -381.0, -175.0, 156
e.wf32(PLAYER + PS_POS, x0); e.wf32(PLAYER + PS_POS + 4, 20.0); e.wf32(PLAYER + PS_POS + 8, z0)
for i in range(6): e.step(0, 0, 0, 2)
segs = json.loads(sys.argv[1])
sx, sy = stick_for(deg0, 80)
for f in range(60):
    e.step(0, sx, sy, 2)
    p = player(e)
    if p['action'] == 34: break
print('stepup at', f, p)
for b, deg, n in segs:
    sx, sy = stick_for(deg, 80) if deg is not None else (0, 0)
    for i in range(n):
        e.step(b if (b != A or i < 12) else 0, sx, sy, 2)
        p = player(e)
        print('x %.2f y %.2f z %.2f' % (p['x'], p['y'], p['z']), p['action'], 'floor', e.s16(COLLISION + 2))
