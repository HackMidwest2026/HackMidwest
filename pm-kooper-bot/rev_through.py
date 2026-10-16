"""pra_01 real side: can the stop-and-go push shove Lakilester up THROUGH the mirror? Mario walks down from the
mirror (Lakilester trails on his north side), then pushes up aimed at him. Prints Lakilester's z and follow state.
usage: rev_through.py DOWN_FRAMES X_SHIFT_FRAMES"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/thr')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
D, XS = int(sys.argv[1]), int(sys.argv[2])
e.load('states/pra01_pushstart.st')
for i in range(XS): e.step(0, 80, 0, 2)
for i in range(D): e.step(0, 0, -80, 2)
for i in range(60): e.step(0, 0, 0, 2)
for c in range(80):
    p, l = player(e), laki()
    deg = math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x']))
    sx, sy = stick_for(deg % 360, 80)
    e.step(0, sx, sy, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    p, l = player(e), laki()
    if c % 5 == 0:
        print(c, 'M %.1f %.1f L %.1f %.1f %.1f st %d spd %.1f' % (p['x'], p['z'], l['x'], l['y'], l['z'], e.u32(0x8010D188) >> 16, l['speed']))
