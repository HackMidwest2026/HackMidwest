"""Which movement direction at the C-down keeps the speed bonus? Mario's recorded point P0 at the strip corner
(884.25, -145); Mario moved 1 unit from it in a screen direction (up = -z, left = -x); Laki planted at the rock-top
turnaround (531, -17, -13) chasing P0. One frame stepped, speed read. usage: speed_dir.py"""
import math, os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/sdir')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
LX, LY, LZ = 531.0, -17.0, -13.0
P0 = (884.25, -145.0)
for label, ang in (('up', 90), ('up, 5 deg to the left', 95), ('up, 10 deg left', 100), ('up, 20 deg left', 110), ('up-left (45)', 135),
                   ('left, 30 deg up', 150), ('left', 180), ('down-left (toward Laki)', 200), ('down', 270), ('right', 0)):
    dx, dz = math.cos(math.radians(ang)), -math.sin(math.radians(ang))     # screen up = -z
    MX, MZ = P0[0] + dx, P0[1] + dz
    e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
    e.wf32(PLAYER + PS_POS, MX); e.wf32(PLAYER + PS_POS + 4, -17.0); e.wf32(PLAYER + PS_POS + 8, MZ)
    for i in range(15): e.step(0, 0, 0, 2)
    p = player(e)
    l = laki(); e.wf32(l['addr'] + 0x38, LX); e.wf32(l['addr'] + 0x3C, LY); e.wf32(l['addr'] + 0x40, LZ)
    e.w32(PTR, 5); e.w32(IDX, 25)
    for k in range(40):
        a = HIST + 16 * k; e.wf32(a + 4, P0[0]); e.wf32(a + 8, -20.0); e.wf32(a + 12, P0[1])
    e.w16(STATE, 0); e.step(0, 0, 0, 2)
    dM = math.hypot(p['x'] - LX, p['z'] - LZ); d = math.hypot(P0[0] - LX, P0[1] - LZ)
    print('%-26s Mario (%.2f, %.2f)  dist to Laki %.2f vs recorded point %.2f  speed %.1f' % (label, p['x'], p['z'], dM, d, laki()['speed']))
