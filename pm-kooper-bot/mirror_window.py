"""pra_02 mirror clip window: push from the left pillar (go G / stop 2) until Mario x >= XS, optionally down 10 /
right 4, then walk up with stick (0, SY) and press C-down on walk-up frame f (0..20). Prints the frames that clip."""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x0400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/mw')
for G in (1, 2, 3):
    for align in (False, True):
        for XS in (700, 712, 720):
            e.load('states/pra02_leftpillar.st')
            for i in range(30): e.step(0, 0, 0, 2)
            while player(e)['x'] < XS:
                for i in range(G): e.step(0, 80, 0, 2)
                e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
            if align:
                for k in range(10): e.step(0, 0, -80, 2)
                for k in range(4): e.step(0, 80, 0, 2)
            e.step(0, 0, 0, 2); e.save('/dev/shm/pmbot/mw/b.st')
            px = player(e)['x']
            for SY in (20, 40):
                ok = []
                for f in range(21):
                    e.load('/dev/shm/pmbot/mw/b.st'); e.step(0, 0, 0, 2)
                    for i in range(f): e.step(0, 0, SY, 2)
                    e.step(CD, 0, SY, 2)
                    for i in range(30): e.step(0, 0, 0, 2)
                    p = player(e)
                    if p['action'] == 33 and p['z'] < -1 and 0 < p['x'] < 1000: ok.append(f)
                print('G%d %s push-to %d (x %.1f) walk-up %d: clipping C-down frames %s' % (G, 'down10/right4' if align else 'straight up  ', XS, px, SY, ok), flush=True)
