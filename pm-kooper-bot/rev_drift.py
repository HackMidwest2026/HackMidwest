"""after rev_push13 end state: stand still N frames and log Lakilester (does he drift back to the stale point?)"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p13')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
e.load('/dev/shm/pmbot/p13/end.st')
for f in range(80):
    e.step(0, 0, 0, 2)
    p, l = player(e), laki()
    if f % 4 == 0: print(f, 'mario %.1f %.1f laki %.1f %.1f %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['y'], l['z'], l['speed']))
