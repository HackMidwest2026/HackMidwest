"""pra_02 behind the mirror: from states/pra02_back_left.st push Lakilester right along the back wall with stop-and-go
(go G frames at stick (80,0), stop S frames) until Mario x >= XEND, then hold down (0,-80) and log Lakilester's speed.
usage: rev_push_back.py G S XEND"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/pb')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
G, S, XEND = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
e.load(os.environ.get('ST', 'states/pra02_back_pillar.st'))
f = 0
for c in range(400):
    for i in range(G): e.step(0, 80, 0, 2)
    for i in range(S): e.step(0, 0, 0, 2)
    f += G + S
    p, l = player(e), laki()
    if c % int(os.environ.get("EVERY", "15")) == 0: print(c, f, 'mario %.1f %.1f laki %.1f %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['z'], l['speed']))
    if p['x'] >= XEND: break
print('push end', f, 'mario %.1f %.1f laki %.1f %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['z'], l['speed']))
for i in range(30):
    e.step(0, 0, -80, 2)
    p, l = player(e), laki()
    print(' down', i, 'mario %.1f %.1f laki %.1f %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['z'], l['speed']))
