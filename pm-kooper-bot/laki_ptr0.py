"""Natural trigger test for the Lakilester stuck/drift glitch: walk right K frames and stand 40 (Laki idles with his
history pointer at P), wiggle in place WIG frames (history keeps recording), then walk left A frames and stand.
Logs pointer/index after each phase and Laki's state/speed/distance while Mario stands at the end.
usage: laki_ptr0.py STATE K [WIG=60] [A=30] [STAND=240]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
st0, K = sys.argv[1], int(sys.argv[2])
WIG = int(sys.argv[3]) if len(sys.argv) > 3 else 60; A = int(sys.argv[4]) if len(sys.argv) > 4 else 30
STAND = int(sys.argv[5]) if len(sys.argv) > 5 else 240
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/lp%d' % os.getpid())
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
def info(t):
    p, l = player(e), laki()
    pt = e.u32(PTR); tx, tz = e.f32(HIST + 16 * pt + 4), e.f32(HIST + 16 * pt + 12)
    print('%-12s state %d ptr %d idx %d  target (%.1f, %.1f)  Mario (%.1f, %.1f) Laki (%.1f, %.1f) dist %.1f speed %.2f' % (t, e.u32(STATE) >> 16, pt, e.u32(IDX), tx, tz, p['x'], p['z'], l['x'], l['z'], math.hypot(p['x'] - l['x'], p['z'] - l['z']), l['speed']))
e.load(st0); e.step(0, 0, 0, 2)
for i in range(K): e.step(0, *stick_for(0, 80), 2)
for i in range(40): e.step(0, 0, 0, 2)
info('idle')
up, dn = stick_for(270, 30), stick_for(90, 30)
for f in range(WIG): e.step(0, *(up if f % 2 == 0 else dn), 2)
for i in range(5): e.step(0, 0, 0, 2)
info('after wiggle')
for i in range(A): e.step(0, *stick_for(180, 80), 2)
info('walked away')
for f in range(STAND):
    e.step(0, 0, 0, 2)
    if f in (20, 60, 120) or f % max(1, STAND // 12) == 0 or f == STAND - 1: info('stand %d' % f)
