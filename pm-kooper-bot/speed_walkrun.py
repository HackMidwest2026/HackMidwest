"""Walking vs running toward the rock: Mario's recorded history point P0 is fixed at the strip corner (884.25, -145);
Mario has since moved D units toward the rock-top turnaround (531, -13) (one walking frame ~2, one running frame
~4.5, several frames). Laki planted at the turnaround chasing P0. One frame stepped, speed read. usage: speed_walkrun.py"""
import math, os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/swr')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
LX, LY, LZ = 531.0, -17.0, -13.0
P0 = (884.25, -145.0)
ux, uz = LX - P0[0], LZ - P0[1]; n = math.hypot(ux, uz); ux, uz = ux / n, uz / n
for label, D in (('no movement (standing on the recorded spot)', 0.0), ('1 unit (tiny nudge)', 1.0), ('1 walking frame (~2)', 2.0),
                 ('1 running frame (~4.5)', 4.5), ('2 walking frames (~4)', 4.0), ('2 running frames (~9)', 9.0), ('4 running frames (~18)', 18.0)):
    MX, MZ = P0[0] + D * ux, P0[1] + D * uz
    e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    e.wf32(PLAYER + PS_POS, MX); e.wf32(PLAYER + PS_POS + 4, -17.0); e.wf32(PLAYER + PS_POS + 8, MZ)
    for i in range(15): e.step(0, 0, 0, 2)
    p = player(e)
    l = laki(); e.wf32(l['addr'] + 0x38, LX); e.wf32(l['addr'] + 0x3C, LY); e.wf32(l['addr'] + 0x40, LZ)
    e.w32(PTR, 5); e.w32(IDX, 25)
    for k in range(40):
        a = HIST + 16 * k; e.wf32(a + 4, P0[0]); e.wf32(a + 8, -20.0); e.wf32(a + 12, P0[1])
    e.w16(STATE, 0); e.step(0, 0, 0, 2)
    print('%-45s Mario (%.1f, %.1f)  dist to Laki %.1f  speed %.1f' % (label, p['x'], p['z'], math.hypot(p['x'] - LX, p['z'] - LZ), laki()['speed']))
