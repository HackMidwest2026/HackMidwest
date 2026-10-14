"""replay every action from one corner-sweep start and list frames where mario is east of x=-100."""
import sys, math
from emu import *
from pm import *
from corner_sweep import stick_for
e = Emu('pm-jp.z64', '/dev/shm/pmbot/probe')
st = sys.argv[1]
found = []
for deg in range(0, 360, 2):
    for mag in (80, 40, 20, 10):
        sx, sy = stick_for(deg, mag)
        for b in (0, 0x20, 0x80, 0x40):
            e.load(st)
            for f in range(25):
                e.step(b if f == 0 else 0, sx, sy, 2)
                p = player(e)
                if p['x'] > -100.5:
                    found.append((p['x'], deg, mag, b, f, p['z'], p['y'], ACTION_NAMES.get(p['action'], p['action']), e.s16(COLLISION + 2)))
found.sort(reverse=True)
print(len(found), 'frames east of x=-100.5')
for r in found[:25]: print('x %.2f deg %d mag %d btn %#x frame %d z %.2f y %.1f %s floor %d' % r)
