"""Log, every frame of an input sequence, Laki's movement (dL), his yaw / isFacingAway / renderYaw, Mario's sprite
facing, the idle-reposition flag D_8010CFCA (JP 0x8010D18A) and follow state. Sequence: greedy push actions (ACTIONS
json) or a raw hold. usage: isk11_facing_probe.py STATE (ACTIONS.json N | hold SX SY N)"""
import json, math, sys
from emu import *
from pm import *
from corner_sweep import stick_for
STATE, CFCA = 0x8010D188, 0x8010D18A
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fp')
lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load(sys.argv[1])
if sys.argv[2] == 'hold':
    seq = [(0, (int(sys.argv[3]), int(sys.argv[4])))] * int(sys.argv[5])
else:
    seq = []
    for d, t, h, w in json.load(open(sys.argv[2]))[:int(sys.argv[3])]:
        seq += [(A if h < 0 else 0, stick_for(d % 360, t))] * abs(h) + [(0, (0, 0))] * w
for f, (b, st) in enumerate(seq):
    l0 = lk(); e.step(b, st[0], st[1], 2); p, l = player(e), lk(); a = l['addr']
    dx, dz = l['x'] - l0['x'], l['z'] - l0['z']
    print('%3d stick %-9s M (%.1f %.1f) face %5.1f | L (%.1f %.1f) d %.2f mv %5.1f deg | yaw %5.1f away %d rYaw %5.1f | st %d cfca %d' % (
        f, st, p['x'], p['z'], e.f32(PLAYER + 0xA8), l['x'], l['z'], math.hypot(dx, dz), math.degrees(math.atan2(dx, -dz)) % 360 if (dx or dz) else -1,
        e.f32(a + 0x0C), e.s16(a + 0x88), e.f32(a + 0x34), e.u32(STATE) >> 16, e.u16(CFCA)))
