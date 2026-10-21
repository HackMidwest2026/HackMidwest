"""Generic scan for the infinite Bombette window: teleport Mario to START (x,y,z) on an out-of-bounds floor next to an
open edge, face world yaw FACE (Bombette walks that way), C-down, then from game frame W hold world yaw OFF (off the
edge) for 40 frames. Reports how long BOMBETTE_3 lasts for each W.
usage: bombette_inf_scan2.py STATE X Y Z FACE OFF W0 W1 [FRAMES]"""
import sys
from emu import *
from pm import *
from nav import stick_world
PSTAT = 0x8010ED70
state = sys.argv[1]; x, y, z, face, off = (float(a) for a in sys.argv[2:7]); w0, w1 = int(sys.argv[7]), int(sys.argv[8])
frames = int(sys.argv[9]) if len(sys.argv) > 9 else 400
e = Emu('pm-jp.z64', '/dev/shm/pmbot/binf2')
e.load(state); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, y); e.wf32(PLAYER + PS_POS + 8, z)
e.step(0, 0, 0, 360)
e.step(0, *stick_world(e, face), 2); e.step(0, 0, 0, 240)
p = player(e); print('start', round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), 'floor', e.s16(COLLISION + 2))
e.step(D_CBUTTON, 0, 0, 2)
e.step(0, 0, 0, 1); base = '/dev/shm/pmbot/binf2_base.st'; e.save(base)
for w in range(w0, w1 + 1):
    e.load(base)
    s3, end3 = None, None
    for f in range(frames):
        st = stick_world(e, off) if w <= f < w + 40 else (0, 0)
        e.step(0, *st, 2)
        s = e.s8(PSTAT)
        if s == 3 and s3 is None: s3 = f
        if s3 is not None and s != 3 and end3 is None: end3 = f
    b = [n for n in npcs(e) if n['id'] == -4]; p = player(e)
    if s3 is None: print('walk %3d: ability never reached BOMBETTE_3' % w); continue
    print('walk %3d: window %s, end state %d bomb y %s mario (%.1f, %.1f, %.1f)' % (
        w, (end3 - s3) if end3 else 'OPEN after %d' % (frames - (s3 or 0)), e.s8(PSTAT), round(b[0]['y'], 1) if b else None, p['x'], p['y'], p['z']), flush=True)
