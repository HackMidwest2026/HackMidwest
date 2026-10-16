"""place Mario at (x, y, z) from a state, C-down with Lakilester speed forced to S; print the mount trace.
usage: t_force.py <state> x y z S"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/tf')
st, x, y, z, S = sys.argv[1], *map(float, sys.argv[2:6])
e.load(st)
e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, y); e.wf32(PLAYER + PS_POS + 8, z)
for i in range(20): e.step(0, 0, 0, 2)
p = player(e); print('placed %.2f %.2f %.2f' % (p['x'], p['y'], p['z']), where(e)[:2])
e.step(0x400, 0, 0, 2)
for i in range(30):
    for n in npcs(e):
        if n['id'] == -4 and player(e)['action'] != 33: e.wf32(n['addr'] + 0x18, S)
    e.step(0, 0, 0, 2)
    p = player(e)
    if i % 3 == 0: print(i, 'act', p['action'], '%.2f %.2f %.2f' % (p['x'], p['y'], p['z']))
