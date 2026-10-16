"""from a push end state, Mario runs in a direction; log Lakilester's speed and positions per frame.
usage: rev_runspeed.py <state> deg [frames]"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rs')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
e.load(sys.argv[1])
sx, sy = stick_for(float(sys.argv[2]), 80)
for f in range(int(sys.argv[3]) if len(sys.argv) > 3 else 60):
    e.step(0, sx, sy, 2)
    p, l = player(e), laki()
    print(f, 'mario %.1f %.1f laki %.1f %.1f %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['y'], l['z'], l['speed']))
