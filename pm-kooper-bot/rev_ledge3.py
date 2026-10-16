"""from states/pra01_corner.st: one or two jumps at the ledge, then the stop-and-go push right on the upper floor.
A jump = hold right W frames, press A (held 8 frames) with the stick at 0 deg for H frames, then neutral until
landed. Variant 'two': first jump W0/H as given by (W1, H1) [pushes Lakilester up the step], second (W2, H2).
After the jumps: stop-and-go right (go G / stop 2) until stuck or lost. Prints the best results by dH.
usage: rev_ledge3.py"""
import math, os, sys, itertools
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, PTR, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D188
A = 0x80
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/ledge3')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
rx, ry = stick_for(0, 80)
def jump(W, H):
    for i in range(W): e.step(0, rx, ry, 2)
    for i in range(24):
        e.step(A if i < 8 else 0, rx if i < H else 0, ry if i < H else 0, 2)
        if i > 3 and player(e)['action'] in (0, 1, 2): break
    for i in range(3): e.step(0, 0, 0, 2)
res = []
jumps = [(W, H) for W in range(0, 6) for H in (0, 2, 4, 6, 8, 10, 12, 14)]
plans = [[j] for j in jumps] + [[(0, 12), j] for j in jumps]
for plan in plans:
    for G in (1, 2):
        e.load('states/pra01_corner.st'); e.step(0, 0, 0, 2)
        ptr0 = e.u32(PTR); tx, tz = e.f32(HIST + 16 * ptr0 + 4), e.f32(HIST + 16 * ptr0 + 12)
        def intact():
            return e.u32(PTR) == ptr0 and e.f32(HIST + 16 * ptr0 + 4) == tx and e.f32(HIST + 16 * ptr0 + 12) == tz and (e.u32(STATE) >> 16) == 5
        ok = True
        for W, H in plan:
            jump(W, H)
            if not intact(): ok = False
        if not ok: continue
        last, stuck, bestd = None, 0, 0
        for c in range(150):
            for i in range(G): e.step(0, rx, ry, 2)
            e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
            if not intact(): break
            l = laki()
            bestd = max(bestd, math.hypot(l['x'] - tx, l['z'] - tz))
        p, l = player(e), laki()
        res.append((round(bestd, 1), plan, G, (round(p['x']), round(p['y']), round(p['z'])), (round(l['x']), round(l['z']))))
res.sort(key=lambda r: -r[0])
for r in res[:15]: print(r)
