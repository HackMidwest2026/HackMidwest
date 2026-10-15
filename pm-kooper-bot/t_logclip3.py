from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jan')
e.load('/dev/shm/pmbot/jan/pre.st')
seq = [(Z, -128, 26)] + [(0x20, -128, 26)] * 4 + [(A | Z, -128, 26)] * 11 + [(A, -128, -100)] * 2
for b, x, y in seq:
    e.step(b, x, y, 2)
p = player(e); print('before crossing frame: x %.3f y %.3f z %.3f' % (p['x'], p['y'], p['z']))
e.save('/dev/shm/pmbot/jan/f17.st')
GCOLL = 0x800B42C0
def collider_flags_addr(cid):
    return e.u32(GCOLL + 4) + cid * 0x1C
def one_frame(label, disable=(), dz=None):
    e.load('/dev/shm/pmbot/jan/f17.st')
    for cid in disable:
        a = collider_flags_addr(cid); e.w32(a, e.u32(a) | 0x10000)
    if dz is not None:
        e.wf32(PLAYER + PS_POS + 8, e.f32(PLAYER + PS_POS + 8) + dz)
    z0 = e.f32(PLAYER + PS_POS + 8)
    e.step(A, -128, -100, 2)
    p = player(e)
    print('%-38s start z %.3f -> x %.3f z %.3f' % (label, z0, p['x'], p['z']))
one_frame('normal')
one_frame('wall 13 (x=-150) off', disable=(13,))
one_frame('wall 27 (z=30 corridor side) off', disable=(27,))
for dz in (-0.5, -0.2, -0.1, 0.0, 0.03, 0.06, 0.1, 0.5):
    one_frame('start z shifted %+.2f' % dz, dz=dz)
one_frame('log slope (collider 26) off', disable=(26,))
one_frame('log slope + wall 13 off', disable=(26, 13))
