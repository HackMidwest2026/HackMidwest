"""kpa_62 (outside Bowser's Castle) Laki remount test: from Mario at (x, z) on the ground, mount Laki (C-down), ride
idle R frames, dismount (C-down), wait W frames, then hold DOWN and press C-down to mount again while holding down for
H frames. Logs Laki speed/yaw at the remount and where Mario ends up.
usage: kpa62_remount.py STATE x z [R=20] [W=20] [H=30] [DISMOUNT=0x400]"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
st0 = sys.argv[1]; X, Z = float(sys.argv[2]), float(sys.argv[3])
R = int(sys.argv[4]) if len(sys.argv) > 4 else 20; W = int(sys.argv[5]) if len(sys.argv) > 5 else 20
H = int(sys.argv[6]) if len(sys.argv) > 6 else 30; DM = int(sys.argv[7], 0) if len(sys.argv) > 7 else 0x400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/k62r%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, X); e.wf32(PLAYER + PS_POS + 8, Z)
for i in range(10): e.step(0, 0, 0, 2)
L = lambda: [q for q in npcs(e) if q['id'] == -4][0]
def show(t):
    p, l = player(e), L()
    print('%-22s M (%7.1f %6.1f %7.1f) act %2d | L (%7.1f %6.1f %7.1f) spd %6.2f yaw %5.0f floor %d' % (t, p['x'], p['y'], p['z'], p['action'], l['x'], l['y'], l['z'], l['speed'], e.f32(l['addr'] + 0xC), e.s16(COLLISION + 2)))
show('start')
e.step(0x400, 0, 0, 2)
for i in range(R + 20): e.step(0, 0, 0, 2)
show('riding')
e.step(DM, 0, 0, 2)
for i in range(W): e.step(0, 0, 0, 2)
show('dismounted')
dn = stick_for(90, 80)
e.step(0, *dn, 2); show('hold down 1f')
e.step(0x400, *dn, 2); show('C-down + down')
for i in range(H):
    e.step(0, *dn, 2)
    if i % 4 == 0: show('  +%d' % i)
for i in range(20): e.step(0, 0, 0, 2)
show('end')
