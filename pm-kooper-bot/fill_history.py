"""Fill Lakilester's history ring at the far left before the push: from a far-left start (Lakilester idle in follow
state 5 on Mario's right), Mario wiggles up/down (1 frame each, stick STEP) staying within the 40-unit tether, until
the ring is full (idx + 1 == ptr) or 120 frames. Then every unconsumed history point is at the far left, so when
Lakilester is released later he turns around there. Prints the ring contents (x range) and saves OUT.
usage: fill_history.py <in.st> <out.st>"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/fill')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
e.load(sys.argv[1]); e.step(0, 0, 0, 2)
ptr0 = e.u32(PTR)
up, dn = stick_for(270, 30), stick_for(90, 30)
for f in range(120):
    e.step(0, *(up if f % 2 == 0 else dn), 2)
    if (e.u32(IDX) + 1) % 40 == e.u32(PTR): break
for i in range(10): e.step(0, 0, 0, 2)
p, l = player(e), laki(); ptr, idx = e.u32(PTR), e.u32(IDX)
pts = [(e.f32(HIST + 16 * k + 4), e.f32(HIST + 16 * k + 12)) for k in range(40)]
order = [(ptr + i) % 40 for i in range(40)]
xs = [pts[k][0] for k in order]
print('frames %d  state %d ptr %d (was %d) idx %d  full %s' % (f + 1, e.u32(STATE) >> 16, ptr, ptr0, idx, (idx + 1) % 40 == ptr))
print('mario %.1f %.1f  laki %.1f %.1f' % (p['x'], p['z'], l['x'], l['z']))
print('target (%.1f, %.1f); ring x range %.1f..%.1f' % (pts[ptr][0], pts[ptr][1], min(xs), max(xs)))
e.step(0, 0, 0, 2); e.save(sys.argv[2])
