"""kpa_62: per-frame trace of one walk-start remount run (same sequence as kpa62_remount_walk.py).
usage: kpa62_trace.py STATE A K W H [DM=0x40] [SEEDX SEEDZ]"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
st0 = sys.argv[1]; A, K, W, H = (int(v) for v in sys.argv[2:6])
DM = int(sys.argv[6], 0) if len(sys.argv) > 6 else 0x40
SX, SZ = (float(v) for v in sys.argv[7:9]) if len(sys.argv) > 8 else (-460.0, -60.0)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/k62t%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, SX); e.wf32(PLAYER + PS_POS + 4, 60.0); e.wf32(PLAYER + PS_POS + 8, SZ)
for i in range(20): e.step(0, 0, 0, 2)
for i in range(K): e.step(0, *stick_for(A, 80), 2)
for i in range(6): e.step(0, 0, 0, 2)
L = lambda: [q for q in npcs(e) if q['id'] == -4][0]
dn = stick_for(90, 80)
seq = [(0x400, 0, 0)] + [(0, 0, 0)] * 40 + [(DM, 0, 0)] + [(0, 0, 0)] * W + [(0,) + dn] * H + [(0x400,) + dn] + [(0,) + dn] * 25 + [(0, 0, 0)] * 10
for f, (b, sx, sy) in enumerate(seq):
    e.step(b, sx, sy, 2)
    p, l = player(e), L()
    if f == 0 or f >= 40:
        print('%3d b%04x M (%7.1f %6.1f %7.1f) act %2d | L (%7.1f %6.1f %7.1f) spd %6.2f yaw %5.0f st %d' % (f, b, p['x'], p['y'], p['z'], p['action'], l['x'], l['y'], l['z'], l['speed'], e.f32(l['addr'] + 0xC), e.u16(0x8010D188)))
