"""from states/pra01_corner.st (Lakilester in the lower floor's top-right corner, pointer 2, target (592, -13)):
walk right 1 frame, jump (A held 8 frames, stick released), then stop-and-go right (go 1 / stop 2) along the top
wall on the upper floor until Lakilester stops at the palace wall. Stops as soon as Lakilester reaches x >= LX (984) and waits HOLD (30) frames.
Saves states/pra01_topright_fast.st (OUT)."""
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
for c in range(150):
    e.step(0, rx, ry, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    if laki()['x'] >= float(os.environ.get('LX', 984)): break      # Lakilester at the palace wall
for i in range(int(os.environ.get('HOLD', 30))): e.step(0, 0, 0, 2)  # about a second, then go
p, l = player(e), laki(); ptr = e.u32(PTR)
print('cycles %d  M (%.1f, %.1f, %.1f) L (%.1f, %.1f, %.1f) state %d ptr %d target (%.1f, %.1f)' % (c + 1, p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, ptr, e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)))
e.save(os.environ.get('OUT', 'states/pra01_topright_fast.st'))
