from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jan')
e.load('/dev/shm/pmbot/jan/pre.st')
seq = [(Z, -128, 26)] + [(0x20, -128, 26)] * 4 + [(A | Z, -128, 26)] * 11 + [(A, -128, -100)] * 10
for i, (b, x, y) in enumerate(seq):
    e.step(b, x, y, 2)
    p = player(e)
    if i >= 13:
        print(i, 'stick', (x, y), ACTION_NAMES.get(p['action'], p['action']), 'x %.3f y %.3f z %.3f' % (p['x'], p['y'], p['z']),
              'speed %.2f targetYaw %.1f' % (p['speed'], e.f32(PLAYER + PS_TARGETYAW)), 'wall', e.s16(COLLISION + 0x12), 'floor', e.s16(COLLISION + 2))
