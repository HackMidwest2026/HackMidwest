"""pra_02 behind the mirror: which lane z and stop-and-go (go G, stop S) keep Lakilester pushed to the right?
Setup per lane: from states/pra02_back_left.st go down D frames, walk left 40 frames (Lakilester trails on the
right, facing left), wait 60. Then push right until Mario x >= 900 or 1500 frames. Reports where Lakilester ended
relative to Mario (pushed = still on his right)."""
import os, itertools
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/ps')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
for D in (0, 2, 4, 8, 16, 30):
    e.load('states/pra02_back_left.st')
    for i in range(D): e.step(0, 0, -80, 2)
    for i in range(40): e.step(0, -80, 0, 2)
    for i in range(60): e.step(0, 0, 0, 2)
    e.save('/dev/shm/pmbot/ps/lane.st')
    p, l = player(e), laki()
    print('lane D=%d mario %.1f %.1f laki %.1f %.1f yaw %.0f' % (D, p['x'], p['z'], l['x'], l['z'], e.f32(l['addr'] + 0x34)), flush=True)
    for G, S in ((1, 2), (2, 2), (3, 2), (4, 2), (2, 3), (3, 3), (5, 3), (1, 1)):
        e.load('/dev/shm/pmbot/ps/lane.st')
        f = 0
        while f < 1500 and player(e)['x'] < 900:
            for i in range(G): e.step(0, 80, 0, 2)
            for i in range(S): e.step(0, 0, 0, 2)
            f += G + S
        p, l = player(e), laki()
        print('   G%d S%d frames %4d mario %.1f %.1f laki %.1f %.1f %s' % (G, S, f, p['x'], p['z'], l['x'], l['z'], 'PUSHED' if l['x'] > p['x'] else ''), flush=True)
