"""Like bombette_inf_scan2.py, but also scans the start distance: START z from Z0 to Z1 (step ZS) at fixed x, and walk
frames W0..W1. Prints Mario's y at Bombette's liftoff, the frame of his respawn, and the window length.
usage: bombette_inf_scan3.py STATE X Y Z0 Z1 ZS FACE OFF W0 W1"""
import sys
from emu import *
from pm import *
from nav import stick_world
PSTAT = 0x8010ED70
state = sys.argv[1]; x, y = float(sys.argv[2]), float(sys.argv[3])
z0, z1, zs = (float(a) for a in sys.argv[4:7]); face, off = float(sys.argv[7]), float(sys.argv[8]); w0, w1 = int(sys.argv[9]), int(sys.argv[10])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/binf3')
z = z0
while z <= z1 + 1e-6:
    e.load(state); e.step(0, 0, 0, 2)
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, y); e.wf32(PLAYER + PS_POS + 8, z)
    e.step(0, 0, 0, 360); e.step(0, *stick_world(e, face), 2); e.step(0, 0, 0, 240)
    e.step(D_CBUTTON, 0, 0, 2); e.step(0, 0, 0, 1); base = '/dev/shm/pmbot/binf3_base.st'; e.save(base)
    for w in range(w0, w1 + 1):
        e.load(base)
        s3 = end3 = lift = resp = None; prevy = player(e)['y']
        for f in range(300):
            e.step(0, *(stick_world(e, off) if w <= f < w + 40 else (0, 0)), 2)
            s = e.s8(PSTAT); p = player(e)
            if s == 3 and s3 is None: s3, lift = f, p['y']
            if s3 is not None and s != 3 and end3 is None: end3 = f
            if p['y'] - prevy > 300 and resp is None: resp = f
            prevy = p['y']
        tag = 'INFINITE' if s3 is not None and end3 is None else ''
        print('z %.1f walk %d: liftoff f%s mario y %s respawn f%s window %s %s' % (z, w, s3, None if lift is None else round(lift, 1), resp, (end3 - s3) if end3 else None, tag), flush=True)
    z += zs
