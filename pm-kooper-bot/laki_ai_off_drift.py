"""Does Laki drift on his own with the follow AI off (state 50) while Mario stands beside him? Teleport Laki to
(LX, LY, LZ), Mario to (MX, MZ), set state 50, then Mario stands still (or holds DIR) for N frames; log Laki.
usage: laki_ai_off_drift.py STATE LX LY LZ MX MZ [N=300] [DIR]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
st0 = sys.argv[1]; LX, LY, LZ, MX, MZ = map(float, sys.argv[2:7]); N = int(sys.argv[7]) if len(sys.argv) > 7 else 300
DIR = float(sys.argv[8]) if len(sys.argv) > 8 else None
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/lad%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2)
l = [n for n in npcs(e) if n['id'] == -4][0]
e.wf32(PLAYER + PS_POS, MX); e.wf32(PLAYER + PS_POS + 8, MZ)
e.wf32(l['addr'] + 0x38, LX); e.wf32(l['addr'] + 0x3C, LY); e.wf32(l['addr'] + 0x40, LZ)
e.w16(STATE, 50)
for f in range(N):
    e.step(0, *(stick_for(DIR, 80) if DIR is not None else (0, 0)), 2)
    if f % (N // 15) == 0 or f == N - 1:
        p = player(e); l = [n for n in npcs(e) if n['id'] == -4][0]
        print('%4d st %d  M (%7.1f %6.1f %7.1f)  L (%7.1f %6.1f %7.1f)  dx %.1f' % (f, e.u32(STATE) >> 16, p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], l['x'] - p['x']))
