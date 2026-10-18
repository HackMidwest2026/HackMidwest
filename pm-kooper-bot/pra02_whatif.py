"""pra_02 what-if: from the far-left filled state, teleport Laki (idle, history intact) to (LX, LZ) and Mario to
(MX, MZ) in RAM, then Mario holds right into the right wall (optionally also down/up), Laki flies back to his stale
target at the far left and turns around. Logs Laki's speed and tries C-down on every frame; reports clips.
usage: pra02_whatif.py LX LZ MX MZ [HOLD=R|RD|RU]"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
CD = 0x400
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
LX, LZ, MX, MZ = map(float, sys.argv[1:5]); HOLD = sys.argv[5] if len(sys.argv) > 5 else 'R'
stick = {'R': stick_for(0, 80), 'RD': stick_for(45, 80), 'RU': stick_for(315, 80), 'N': (0, 0)}[HOLD]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p2wi')
w = '/dev/shm/pmbot/p2wi'
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
e.load('states/pra02_left_full.st'); e.step(0, 0, 0, 2)
l = laki(); e.wf32(l['addr'] + 0x38, LX); e.wf32(l['addr'] + 0x40, LZ)
e.wf32(PLAYER + PS_POS, MX); e.wf32(PLAYER + PS_POS + 8, MZ)
e.step(0, 0, 0, 2)
best, clips = 0, []
for f in range(150):
    e.save(w + '/s.st')
    e.step(CD, *stick, 2); spd = laki()['speed']
    if spd > 100:
        q = player(e)
        for i in range(40): e.step(0, 0, 0, 2)
        if player(e)['z'] > 1: clips.append((f, round(spd, 1)))
    best = max(best, spd)
    e.load(w + '/s.st'); e.step(0, *stick, 2)
    p, l = player(e), laki()
    if f % 10 == 0 or (100 < l['speed']): print(f, 'M (%.1f, %.1f) L (%.1f, %.1f, %.1f) spd %.1f st %d ptr %d' % (p['x'], p['z'], l['x'], l['y'], l['z'], l['speed'], e.u32(STATE) >> 16, e.u32(PTR)))
print('best C-down speed %.1f; clips %s' % (best, clips))
