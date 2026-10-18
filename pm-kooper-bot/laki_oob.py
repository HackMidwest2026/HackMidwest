"""mac_01 (Toad Town plaza, Rowf's shop) left entrance: walk off the floor edge into the void and log Mario and
Lakilester (follow state, history pointer/index, target, speed) every EVERY frames.
usage: laki_oob.py STATE DIR N_WALK N_AFTER [EVERY=10] [MX MY MZ]  (optional: teleport Mario there first)  (DIR = stick angle: 0 right, 90 down, 180 left, 270 up)"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
st0 = sys.argv[1]; D, NW, NA = float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
EVERY = int(sys.argv[5]) if len(sys.argv) > 5 else 10
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/oob%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2)
if len(sys.argv) > 8:
    for k, v in enumerate(map(float, sys.argv[6:9])): e.wf32(PLAYER + PS_POS + 4 * k, v)
for f in range(NW + NA):
    e.step(0, *(stick_for(D, 80) if f < NW else (0, 0)), 2)
    if f % EVERY == 0 or f == NW + NA - 1:
        p = player(e); ls = [n for n in npcs(e) if n['id'] == -4]; pt = e.u32(PTR)
        l = ls[0] if ls else {'x': 0, 'y': 0, 'z': 0, 'speed': 0}
        print('%4d M (%7.1f %8.1f %7.1f) act %2d | L (%7.1f %8.1f %7.1f) st %2d ptr %2d idx %2d tgt (%7.1f %8.1f %7.1f) spd %6.2f mode %d map %s' % (
            f, p['x'], p['y'], p['z'], p['action'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, pt, e.u32(IDX),
            e.f32(HIST + 16 * pt + 4), e.f32(HIST + 16 * pt + 8), e.f32(HIST + 16 * pt + 12), l['speed'], e.s16(GAME_MODE), where(e)))
