"""pra_02 mirror clip as simple inputs: stop-and-go push (go 1 / stop 2) from the left pillar until Mario x >= XSTOP,
then: down for D frames, right for R frames, then up with stick (0, U), pressing C-down on frame k of the up walk.
Prints which k clip for each (XSTOP, D, R, U), plus Lakilester's speed on that frame."""
import os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x0400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/mroute')


def laki():
    for n in npcs(e):
        if n['id'] == -4: return n


best = []
for xstop in (712.0, 718.0, 724.0):
    e.load('states/pra02_leftpillar.st')
    for c in range(250):
        if player(e)['x'] >= xstop: break
        e.step(0, 80, 0, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    e.step(0, 0, 0, 2)
    base = '/dev/shm/pmbot/mroute/base.st'; e.save(base)
    for D in (4, 6, 8, 10):
        for R in (4, 6, 8, 10, 12):
            for U in (20, 40, 80):
                e.load(base)
                for i in range(D): e.step(0, 0, -80, 2)
                for i in range(R): e.step(0, 80, 0, 2)
                pre = '/dev/shm/pmbot/mroute/pre.st'; e.save(pre)
                ks = []
                for k in range(0, 25):
                    e.load(pre)
                    for i in range(k): e.step(0, 0, U, 2)
                    pk, s = player(e), laki()['speed']
                    e.step(CD, 0, U, 2)
                    for i in range(28): e.step(0, 0, 0, 2)
                    p = player(e)
                    if p['action'] == 33 and p['z'] < -1:
                        ks.append((k, round(s, 1), round(pk['x'], 1), round(pk['z'], 1)))
                if ks:
                    best.append((len(ks), xstop, D, R, U, ks))
                    print('push to %.0f, down %d, right %d, up (0,%d): C-down frames that clip %s' % (xstop, D, R, U, ks), flush=True)
best.sort(key=lambda b: -b[0])
print('most forgiving:', best[:3])
