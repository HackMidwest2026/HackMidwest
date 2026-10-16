"""after the back-wall push (go 1 / stop 2 until Mario x >= XEND), try release paths and log Lakilester's peak speed
and Mario's position on that frame. usage: rev_release.py XEND"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rr2')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
XEND = float(sys.argv[1])
e.load('states/pra02_back_pillar.st')
while player(e)['x'] < XEND:
    e.step(0, 80, 0, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
e.step(0, 0, 0, 2); e.save('/dev/shm/pmbot/rr2/end.st')
for deg in range(0, 360, 30):
    for mag in (80, 30):
        e.load('/dev/shm/pmbot/rr2/end.st'); e.step(0, 0, 0, 2)
        sx, sy = stick_for(deg, mag)
        best = (0, 0, 0, 0)
        for f in range(90):
            e.step(0, sx, sy, 2)
            l, p = laki(), player(e)
            if l['speed'] > best[0]: best = (round(l['speed'], 1), f, round(p['x'], 1), round(p['z'], 1))
        print(deg, mag, 'peak spd %.1f at frame %d mario (%.1f, %.1f)' % best)
