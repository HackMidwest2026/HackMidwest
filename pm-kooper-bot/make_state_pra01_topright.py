"""from states/pra01_corner.st (Lakilester in the lower floor's top-right corner, pointer 2, target (592, -13)):
walk right 1 frame, jump (A held 8 frames, stick released), then stop-and-go right (go 1 / stop 2) along the top
wall on the upper floor until Lakilester stops at the palace wall. Saves states/pra01_topright.st."""
import math, os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, PTR, STATE = 0x8010CEF8, 0x8010D17C, 0x8010D188
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/mktr2')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
rx, ry = stick_for(0, 80)
e.load('states/pra01_corner.st'); e.step(0, 0, 0, 2)
e.step(0, rx, ry, 2)
for i in range(24):
    e.step(0x80 if i < 8 else 0, 0, 0, 2)
    if i > 3 and player(e)['action'] in (0, 1, 2): break
for i in range(3): e.step(0, 0, 0, 2)
p, l = player(e), laki(); print('after jump M (%.1f, %.1f, %.1f) L (%.1f, %.1f, %.1f)' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z']))
lastx, still = None, 0
for c in range(150):
    e.step(0, rx, ry, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    l = laki()
    still = still + 1 if lastx is not None and abs(l['x'] - lastx) < 0.01 else 0
    lastx = l['x']
    if still >= 5: break
p, l = player(e), laki(); ptr = e.u32(PTR)
print('cycles %d  M (%.1f, %.1f, %.1f) L (%.1f, %.1f, %.1f) state %d ptr %d target (%.1f, %.1f)' % (c + 1, p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, ptr, e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)))
e.save('states/pra01_topright.st')
