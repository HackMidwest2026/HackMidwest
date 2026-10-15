"""probe the blue house's leaning east wall: jump beside it and log every frame."""
import os, sys
from emu import Emu
from pm import *
from corner_sweep import stick_for
A, Z = 0x0080, 0x0020
e = Emu(os.environ.get('PM_ROM', 'pm-jp.z64'), '/dev/shm/pmbot/house')
e.load('states/mac02_start.st')
e.step(0, 0, 0, 2)
x0, z0, deg = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
spin = len(sys.argv) > 4 and sys.argv[4] == 'spin'
e.wf32(PLAYER + PS_POS, x0); e.wf32(PLAYER + PS_POS + 4, 20.0); e.wf32(PLAYER + PS_POS + 8, z0)
for i in range(6): e.step(0, 0, 0, 2)
sx, sy = stick_for(deg, 80)
for f in range(40):
    b = (Z if f == 0 else (A if 2 <= f < 14 else 0)) if spin else (A if f < 12 else 0)
    e.step(b, sx, sy, 2)
    p = player(e)
    print(f, 'x %.2f y %.2f z %.2f' % (p['x'], p['y'], p['z']), ACTION_NAMES.get(p['action'], p['action']),
          'floor', e.s16(COLLISION + 2), 'cur', e.s16(COLLISION + 4), 'wall', e.s16(COLLISION))
