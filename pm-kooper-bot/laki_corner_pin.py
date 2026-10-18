"""Synthetic test of the "pinned while Mario moves" idea: put Laki at (LX, LZ) near a corner, point his history target
at (TX, TZ) beyond the walls, mark the ring full (idx = ptr - 1), then walk Mario around and log Laki.
usage: laki_corner_pin.py STATE LX LZ TX TZ"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
st0 = sys.argv[1]; LX, LZ, TX, TZ = map(float, sys.argv[2:6])
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/lcp%d' % os.getpid())
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
e.load(st0); e.step(0, 0, 0, 2)
l = laki(); p = player(e)
e.wf32(l['addr'] + 0x38, LX); e.wf32(l['addr'] + 0x40, LZ)
for k in range(40):  # every entry: the far target
    e.wf32(HIST + 16 * k + 4, TX); e.wf32(HIST + 16 * k + 8, p['y']); e.wf32(HIST + 16 * k + 12, TZ)
e.w32(PTR, 10); e.w32(IDX, 9); e.w32(STATE, 0)
seq = [(0, 0)] * 60 + [stick_for(0, 80)] * 40 + [stick_for(90, 80)] * 20 + [stick_for(180, 80)] * 60 + [(0, 0)] * 120
for f, s in enumerate(seq):
    e.step(0, *s, 2); l = laki(); p = player(e); pt = e.u32(PTR)
    if f % 10 == 0 or f < 5:
        print('%3d M (%7.1f %7.1f) L (%7.1f %5.1f %7.1f) st %d ptr %d idx %d tgt (%.0f %.0f) spd %.2f fl %08x dM %.1f' % (f, p['x'], p['z'], l['x'], l['y'], l['z'],
              e.u32(STATE) >> 16, pt, e.u32(IDX), e.f32(HIST + 16 * pt + 4), e.f32(HIST + 16 * pt + 12), l['speed'], l['flags'], math.hypot(p['x'] - l['x'], p['z'] - l['z'])))
