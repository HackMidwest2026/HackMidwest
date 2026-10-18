"""pra_02 back side: which forced Laki speeds clip from the right-wall strip (x ~980, z -13..-68)? Places Mario, C-down
with Laki's speed forced to S, rides 40 frames, and checks for the front side (z > 1). usage: pra02_strip_window.py"""
import os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p2w')
w = '/dev/shm/pmbot/p2w'
e.load('states/pra02_back_pillar.st'); e.step(0, 0, 0, 2); e.save(w + '/b.st')
for x, z in ((980.5, -20), (980.5, -40), (980.5, -60), (981.0, -30), (982.0, -40), (978.0, -40)):
    row = []
    for S in range(150, 401, 10):
        e.load(w + '/b.st')
        e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, float(z))
        for i in range(12): e.step(0, 0, 0, 2)
        e.step(CD, 0, 0, 2)
        for i in range(40):
            for n in npcs(e):
                if n['id'] == -4 and player(e)['action'] != 33: e.wf32(n['addr'] + 0x18, float(S))
            e.step(0, 0, 0, 2)
        row.append('Y' if player(e)['z'] > 1 else '.')
    print('(%.1f, %d) speeds 150..400 step 10: %s' % (x, z, ''.join(row)), flush=True)
