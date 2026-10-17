"""Does Mario moving at the C-down change Laki's speed? Laki planted at the rock-top turnaround (531, -17, -13) in
follow state 0 with his next history point P; Mario standing at M. Cases: P = M (Mario standing still: his newest
history point is where he is), P 5 units farther from Laki than M (Mario walking toward Laki/the rock), P 5 units
closer (walking away). Also Mario at near-mirror spots. One frame stepped, speed read. usage: speed_moving.py"""
import math, os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/smv')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
LX, LY, LZ = 531.0, -17.0, -13.0
def trial(MX, MY, MZ, off):
    e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    e.wf32(PLAYER + PS_POS, MX); e.wf32(PLAYER + PS_POS + 4, MY + 3); e.wf32(PLAYER + PS_POS + 8, MZ)
    for i in range(15): e.step(0, 0, 0, 2)
    p = player(e)
    ux, uz = (p['x'] - LX), (p['z'] - LZ); n = math.hypot(ux, uz); ux, uz = ux / n, uz / n
    hx, hz = p['x'] + off * ux, p['z'] + off * uz
    l = laki(); e.wf32(l['addr'] + 0x38, LX); e.wf32(l['addr'] + 0x3C, LY); e.wf32(l['addr'] + 0x40, LZ)
    e.w32(PTR, 5); e.w32(IDX, 25)
    for k in range(40):
        a = HIST + 16 * k; e.wf32(a + 4, hx); e.wf32(a + 8, p['y']); e.wf32(a + 12, hz)
    e.w16(STATE, 0); e.step(0, 0, 0, 2)
    return laki()['speed'], math.hypot(p['x'] - LX, p['z'] - LZ)
for name, (MX, MY, MZ) in (('strip corner', (882.7, -20.0, -144.7)), ('strip middle', (876.0, -20.0, -110.0)),
                           ('near mirror', (820.0, -30.0, -18.0)), ('near mirror', (780.0, -30.0, -20.0))):
    for label, off in (('standing still (newest point = Mario)', 0.0), ('walking toward Laki (point 5 farther)', 5.0), ('walking away (point 5 closer)', -5.0)):
        s, dM = trial(MX, MY, MZ, off)
        print('%-12s (%.0f, %.0f)  dist %.0f  %-40s speed %.1f' % (name, MX, MZ, dM, label, s))
