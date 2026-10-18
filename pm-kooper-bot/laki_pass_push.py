"""Measure Laki's world displacement when Mario walks through him with the follow AI off (state 50): Laki at
(LX, LY, LZ), Mario starts at (MX, MZ) and alternately holds left/right for K frames, N passes. Logs every frame where
Laki moved. usage: laki_pass_push.py STATE LX LY LZ MX MZ [K=30] [N=6] [FIRST=0]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
st0 = sys.argv[1]; LX, LY, LZ, MX, MZ = map(float, sys.argv[2:7])
K = int(sys.argv[7]) if len(sys.argv) > 7 else 30; N = int(sys.argv[8]) if len(sys.argv) > 8 else 6
FIRST = float(sys.argv[9]) if len(sys.argv) > 9 else 0
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/lpp%d' % os.getpid())
e.load(st0); e.step(0, 0, 0, 2)
l = [n for n in npcs(e) if n['id'] == -4][0]
e.wf32(PLAYER + PS_POS, MX); e.wf32(PLAYER + PS_POS + 8, MZ)
e.wf32(l['addr'] + 0x38, LX); e.wf32(l['addr'] + 0x3C, LY); e.wf32(l['addr'] + 0x40, LZ)
e.w16(STATE, 50); e.step(0, 0, 0, 2)
prev = None; f = 0
for k in range(N):
    d = FIRST if k % 2 == 0 else (FIRST + 180) % 360
    for i in range(K):
        e.step(0, *stick_for(d, 80), 2); f += 1
        p = player(e); l = [n for n in npcs(e) if n['id'] == -4][0]; cur = (l['x'], l['y'], l['z'])
        if prev and math.dist(cur, prev) > 0.01:
            print('f%3d pass %d (Mario %s) M (%6.1f %5.1f %6.1f)  L (%6.1f %5.1f %6.1f)  moved dx %+.2f dz %+.2f' % (f, k, 'right' if d == 0 else 'left' if d == 180 else d,
                  p['x'], p['y'], p['z'], *cur, cur[0] - prev[0], cur[2] - prev[2]))
        prev = cur
    print('-- end pass %d: Laki (%.1f, %.1f)' % (k, prev[0], prev[2]))
