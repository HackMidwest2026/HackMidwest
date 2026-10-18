"""Classify Laki after a skewed flo_08 entry: wait 150 frames, then walk right 40, stand 20, left 25, stand 20, right 25, stand 20;
report Laki's world displacement in each phase, his height above Mario, follow state and pointer/index."""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
STATE, PTR, IDX = 0x8010D188, 0x8010D17C, 0x8010D178
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/spr%d' % os.getpid())
e.load(sys.argv[1])
L = lambda: [q for q in npcs(e) if q['id'] == -4][0]
for i in range(150): e.step(0, 0, 0, 2)
out = []
for d, n in ((0, 40), (None, 20), (180, 25), (None, 20), (0, 25), (None, 20)):
    p0, l0 = player(e), L()
    for i in range(n): e.step(0, *(stick_for(d, 80) if d is not None else (0, 0)), 2)
    p1, l1 = player(e), L()
    out.append('%s M %+6.1f L %+6.1f,%+6.1f' % ({180: 'L', 0: 'R', None: 'S'}[d], p1['x'] - p0['x'], l1['x'] - l0['x'], l1['z'] - l0['z']))
p, l = player(e), L()
print('T %6s | %s | Laki h %+6.1f st %d ptr %d idx %d spd %.1f M (%.0f,%.0f,%.0f) map %s' % (sys.argv[2], ' | '.join(out), l['y'] - p['y'], e.u32(STATE) >> 16, e.u32(PTR), e.u32(IDX), l['speed'], p['x'], p['y'], p['z'], where(e)))
