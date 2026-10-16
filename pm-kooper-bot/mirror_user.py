"""pra_02 mirror clip, the user's method: stop-and-go push from the left pillar to the right pillar (go 1 / stop 2,
stopping once Mario x >= XSTOP), then walk up slowly with stick (sx, UP) and press C-down on frame k.
Prints every (xstop, stick, k) that ends with Mario riding Lakilester behind the mirror (z < 0)."""
import os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x0400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/mu')


def laki():
    for n in npcs(e):
        if n['id'] == -4: return n


tot, hits = 0, []
for xstop in (716.0, 718.0, 720.0, 722.0, 724.0, 726.0, 727.0, 728.0, 729.0):
    e.load('states/pra02_leftpillar.st')
    for c in range(250):
        if player(e)['x'] >= xstop: break
        e.step(0, 80, 0, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    e.step(0, 0, 0, 2)
    base = '/dev/shm/pmbot/mu/base.st'; e.save(base)
    p0 = player(e)
    for sx in (0, 2, 4, 6):
        for up in (8, 10, 12, 16, 20, 30):
            ks = []
            for k in range(0, 45):
                e.load(base)
                for i in range(k): e.step(0, sx, up, 2)
                spd = laki()['speed']
                e.step(CD, sx, up, 2)
                for i in range(25): e.step(0, 0, 0, 2)
                p = player(e)
                tot += 1
                if p['action'] == 33 and p['z'] < -1 and 0 < p['x'] < 1000:
                    ks.append((k, round(spd, 1), round(p['x']), round(p['z'])))
            if ks:
                hits.append((xstop, sx, up, ks))
                print('push to x %.2f (mario at %.2f, %.2f), walk up stick (%d, %d): C-down frames that clip %s' % (
                    xstop, p0['x'], p0['z'], sx, up, ks), flush=True)
print('%d tries, %d (setup, stick) combinations clip' % (tot, len(hits)))
