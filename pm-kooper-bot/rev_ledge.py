"""pra_01 reflected side, from the corner (states/pra01_corner.st, Lakilester against the top wall at the step):
jump (A) while holding the stick at JDEG, keep holding H frames, then continue the stop-and-go push (go G / stop S)
at PDEG along the top wall. Logs follow state, pointer, whether the stale target is intact, and dH.
usage: rev_ledge.py JDEG H PDEG G S [cycles] [save]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, PTR, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D188
A = 0x80
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/ledge')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
JDEG, H, PDEG, G, S = float(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
N = int(sys.argv[6]) if len(sys.argv) > 6 else 80
e.load(os.environ.get('ST', 'states/pra01_corner.st')); e.step(0, 0, 0, 2)
ptr0 = e.u32(PTR); tx, tz = e.f32(HIST + 16 * ptr0 + 4), e.f32(HIST + 16 * ptr0 + 12)
def st(tag):
    p, l = player(e), laki()
    ptr = e.u32(PTR); ok = ptr == ptr0 and e.f32(HIST + 16 * ptr + 4) == tx and e.f32(HIST + 16 * ptr + 12) == tz
    print(tag, 'M %.1f %.1f %.1f L %.1f %.1f %.1f st %d ptr %d %s dH %.1f spd %.1f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, ptr, 'intact' if ok else 'LOST', math.hypot(l['x'] - tx, l['z'] - tz), l['speed']), flush=True)
    return ok
jx, jy = stick_for(JDEG, 80)
e.step(A, jx, jy, 2)
for i in range(H):
    e.step(A, jx, jy, 2)
    if i % 4 == 3: st('air %d' % i)
for i in range(6): e.step(0, 0, 0, 2)
st('landed')
px, py = stick_for(PDEG, 80)
for c in range(N):
    for i in range(G): e.step(0, px, py, 2)
    for i in range(S): e.step(0, 0, 0, 2)
    if c % 10 == 9:
        if not st('push %d' % c): break
st('end')
if len(sys.argv) > 7: e.save(sys.argv[7])
