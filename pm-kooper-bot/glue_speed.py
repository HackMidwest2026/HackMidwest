"""Glued-Laki speed test: in the glued state (Laki snapped onto Mario every frame, chasing a stale out-of-bounds
history entry) his moveSpeed is 3 + dT/16, dT = horizontal distance to that entry. Walk Mario in direction DIR for N
frames, log Laki's speed vs distance to his target, then C-down and log Mario's displacement during the mount.
usage: glue_speed.py STATE DIR N [CDOWN=1]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, PTR, IDX, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D178, 0x8010D188
st0, D, N = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]); CD = int(sys.argv[4]) if len(sys.argv) > 4 else 1
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/gsp%d' % os.getpid())
e.load(st0)
for i in range(150): e.step(0, 0, 0, 2)
def show(t):
    p = player(e); l = [q for q in npcs(e) if q['id'] == -4][0]; pt = e.u32(PTR)
    tx, ty, tz = e.f32(HIST + 16 * pt + 4), e.f32(HIST + 16 * pt + 8), e.f32(HIST + 16 * pt + 12)
    dT = math.hypot(l['x'] - tx, l['z'] - tz)
    print('%-10s st %d M (%7.1f %6.1f %6.1f) act %2d L (%7.1f %6.1f) spd %7.2f  target (%.0f %.0f %.0f) dT %.0f -> 3+dT/16 = %.1f' % (t, e.u32(STATE) >> 16, p['x'], p['y'], p['z'], p['action'], l['x'], l['y'], l['speed'], tx, ty, tz, dT, 3 + dT / 16))
show('start')
for i in range(N):
    e.step(0, *stick_for(D, 80), 2)
    if i % 40 == 0: show('walk %d' % i)
for i in range(5): e.step(0, 0, 0, 2)
show('stop')
if CD:
    p0 = player(e)
    e.step(0x400, 0, 0, 2)
    for i in range(40):
        e.step(0, 0, 0, 2)
        if i % 4 == 0: p = player(e); print('  mount +%2d  M (%7.1f %6.1f %6.1f) act %d  moved %.1f' % (i, p['x'], p['y'], p['z'], p['action'], math.hypot(p['x'] - p0['x'], p['z'] - p0['z'])))
