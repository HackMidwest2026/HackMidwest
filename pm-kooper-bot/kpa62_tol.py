"""kpa_62 remount clip: tolerance of the dismount spot. Mario is placed (RAM) at (x, 60, z) on the y-60 platform, mounts
Laki, rides idle 40 frames, dismounts (B = frame 0), holds notch D from frame 1 and presses C-down on frame T.
Prints a map of which start spots clip for each T.
usage: kpa62_tol.py STATE CX CZ HALF STEP D [T...]   env: ZHALF, ZSTEP (separate z range)"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
st0 = sys.argv[1]; CX, CZ, HALF, STEP = (float(v) for v in sys.argv[2:6]); D = int(sys.argv[6])
TS = [int(v) for v in sys.argv[7:]] or [33, 34, 35]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/ktol%d' % os.getpid())
tmp = '/dev/shm/pmbot/ktol%d' % os.getpid()
e.load(st0); e.step(0, 0, 0, 2); e.save(tmp + '.base')
n = int(round(2 * HALF / STEP)) + 1
ZH, ZS = float(os.environ.get('ZHALF', HALF)), float(os.environ.get('ZSTEP', STEP))
zs = [CZ - ZH + i * ZS for i in range(int(round(2 * ZH / ZS)) + 1)]; xs = [CX - HALF + i * STEP for i in range(n)]
rows = {}
for z in zs:
    for x in xs:
        e.load(tmp + '.base')
        e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 60.0); e.wf32(PLAYER + PS_POS + 8, z)
        idle = 0                                         # let Laki catch up and settle, as in a real run
        for i in range(900):
            e.step(0, 0, 0, 2)
            idle = idle + 1 if [q for q in npcs(e) if q['id'] == -4][0]['speed'] == 0 else 0
            if idle >= 10: break
        p = player(e)
        if abs(p['x'] - x) > .05 or abs(p['z'] - z) > .05 or abs(p['y'] - 60) > .5: rows[(x, z)] = '#'; continue
        e.step(0x400, 0, 0, 2)
        for i in range(40): e.step(0, 0, 0, 2)
        e.step(0x40, 0, 0, 2); e.save(tmp + '.dis')
        res = ''
        for T in TS:
            e.load(tmp + '.dis')
            for fr in range(1, T): e.step(0, *stick_for(D, 80), 2)
            e.step(0x400, *stick_for(D, 80), 2); ok = False
            for f in range(30):
                e.step(0, *stick_for(D, 80), 2); q = player(e)
                if f > 18 and q['y'] > 40 and inside_tower(q['x'], q['z']): ok = True; break
            if ok: res += str(T % 10)
        rows[(x, z)] = res[:1] if res else '.'
print('start-spot map around (%.1f, %.1f), step %.2f, hold %d; digit = last digit of first working T, # = not standable' % (CX, CZ, STEP, D))
print('        ' + ''.join('%-8.1f' % x for x in xs[::8]))
for z in zs:
    print('%7.1f ' % z + ''.join(rows[(x, z)] for x in xs))
