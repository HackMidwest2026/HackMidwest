"""pra_18: can a C-down mount (steps -z,+x,+z,-x of length = Laki speed, tested with LAKI's radius) put Mario closer to the
mirror than walking (13 units) and inside Clubba 3's 80-unit trigger from the north side?
DIAGNOSTIC: Mario placed at (x, -13.5); Laki speed forced to S until the mount (same method as pra18_mount_fine.py)."""
import os, sys, math
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mt%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2); b0 = '/dev/shm/pmbot/mt%d.st' % os.getpid(); e.save(b0)
L = laki(); print('laki collision height/diameter', e.u16(L['addr'] + 0xA8) if hasattr(e, 'u16') else '?')
best = (1e9,)
for x in range(700, 740, 3):
    for S in (2, 4, 6, 8, 12, 16, 20, 30, 40):
        e.load(b0)
        e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 8, -13.5)
        for i in range(20): e.step(0, 0, 0, 2)
        e.step(D_CBUTTON, 0, 0, 2); m = (1e9, None)
        for i in range(40):
            if player(e)['action'] != 33: e.wf32(laki()['addr'] + 0x18, float(S))
            e.step(0, 0, 0, 2); p = player(e); d = math.hypot(p['x'] - 717, p['z'] - 70)
            if d < m[0]: m = (d, round(p['x'], 2), round(p['z'], 2), i, e.s32(0x800DC048) if False else '')
        gs = game_status(e) if 'game_status' in dir() else ''
        if m[0] < best[0]: best = (m[0], x, S, m)
        if m[0] < 82.5: print('x', x, 'S', S, 'min dist %.2f at (%s, %s) frame %d' % m[:4], flush=True)
print('best', best)
