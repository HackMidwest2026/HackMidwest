"""from states/pra01_corner.st: hold right W frames, jump (A held for HA frames) holding the stick at JDEG, keep the
stick H frames total, then stop-and-go right (go G / stop 2) along the top wall on the upper floor.
Sweep W, HA, JDEG; print where Mario/Lakilester end and whether the frozen target survived.
usage: rev_ledge2.py [save_best]"""
import math, os, sys, itertools
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, PTR, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D188
A = 0x80
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/ledge2')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
best = None
for W, HA, JDEG, G in itertools.product((0, 2, 4, 6, 8), (6, 12), (0, 345, 330), (1, 2)):
    e.load('states/pra01_corner.st'); e.step(0, 0, 0, 2)
    ptr0 = e.u32(PTR); tx, tz = e.f32(HIST + 16 * ptr0 + 4), e.f32(HIST + 16 * ptr0 + 12)
    def intact():
        return e.u32(PTR) == ptr0 and e.f32(HIST + 16 * ptr0 + 4) == tx and e.f32(HIST + 16 * ptr0 + 12) == tz and (e.u32(STATE) >> 16) == 5
    rx, ry = stick_for(0, 80); jx, jy = stick_for(JDEG, 80)
    ok = True
    for i in range(W): e.step(0, rx, ry, 2)
    for i in range(20):
        e.step(A if i < HA else 0, jx, jy, 2)
    for i in range(4): e.step(0, 0, 0, 2)
    p = player(e)
    up = p['y'] > -40
    for c in range(120):
        for i in range(G): e.step(0, rx, ry, 2)
        e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
        if not intact(): ok = False; break
    p, l = player(e), laki()
    dH = math.hypot(l['x'] - tx, l['z'] - tz)
    print('W%d A%d jump%3d G%d: mario on ledge %s, end M (%.0f,%.0f,%.0f) L (%.0f,%.0f) %s dH %.0f' % (W, HA, JDEG, G, up, p['x'], p['y'], p['z'], l['x'], l['z'], 'intact' if ok else 'LOST at c%d' % c, dH), flush=True)
    if ok and (best is None or dH > best[0]): best = (dH, (W, HA, JDEG, G))
print('best', best)
