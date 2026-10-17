"""Check the follow-speed formula directly: put Mario in the stair strip, put Lakilester at (LX, LZ) in follow state 0
chasing history entry P set to (HX, HY, HZ), step one frame, read his speed. Compares with
 s = 0.25*dM (dM >= 50, Laki not below Mario), then vs entry distance d: s = 0.25*d if s >= 0.25*d else s + d/16.
usage: speed_bound.py"""
import math, os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/sb')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
MX, MY, MZ = 878.0, -20.0, -108.0
e.load('states/pra01_topright.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, MX); e.wf32(PLAYER + PS_POS + 4, MY + 3); e.wf32(PLAYER + PS_POS + 8, MZ)
for i in range(15): e.step(0, 0, 0, 2)
p = player(e); print('Mario', round(p['x'], 1), round(p['y'], 1), round(p['z'], 1))
e.save('/dev/shm/pmbot/sb/base.st')
def trial(LX, LY, LZ, HX, HY, HZ):
    e.load('/dev/shm/pmbot/sb/base.st'); e.step(0, 0, 0, 2)
    l = laki()
    e.wf32(l['addr'] + 0x38, LX); e.wf32(l['addr'] + 0x3C, LY); e.wf32(l['addr'] + 0x40, LZ)
    ptr = 5
    e.w32(PTR, ptr); e.w32(IDX, 20)
    for k in range(40):
        a = HIST + 16 * k
        e.wf32(a + 4, HX); e.wf32(a + 8, HY); e.wf32(a + 12, HZ)
    e.w16(STATE, 0)
    e.step(0, 0, 0, 2)
    l, p = laki(), player(e)
    return l['speed']
def model(LX, LY, LZ, HX, HZ):
    dM = math.hypot(LX - MX, LZ - MZ); d = math.hypot(LX - HX, LZ - HZ)
    s = 3.0
    if dM >= 50: s = 0.25 * dM if LY >= MY else 8.0
    if s < d:
        if LY >= MY: s = 0.25 * d if s >= 0.25 * d else s + d / 16
        else: s = 6.0 if s > 6 else s + 1
    return s, dM, d
for LX, LZ in ((510, -200), (510, -60), (530, -150), (560, -40), (600, -100), (650, -150)):
    for HX, HY, HZ in ((985, -30, -205), (960, 0, -150), (700, -60, -150)):
        for LY in (-10.0, -40.0):
            s = trial(LX, LY, LZ, HX, HY, HZ); m, dM, d = model(LX, LY, LZ, HX, HZ)
            print('Laki (%d, %d, y %d) entry (%d, %d): measured %.1f  model %.1f   dM %.0f d %.0f' % (LX, LZ, LY, HX, HZ, s, m, dM, d))
