"""pra_02 back side, far-left mid-depth fill: from states/pra02_back_left.st (Mario at the far left by the back wall,
Laki on his right) walk right R frames, down D frames, then left back to the left wall (Laki trails in on his
right), stand W frames until Laki is idle (state 5), then wiggle up/down until the history ring is full.
Saves OUT when Laki ends idle on Mario's right with the ring full. usage: make_state_pra02_mid.py R D W OUT"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D17C, 0x8010D188
R, D, W, OUT = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p2m%d' % os.getpid())
laki = lambda: [n for n in npcs(e) if n['id'] == -4][0]
e.load('states/pra02_back_left.st'); e.step(0, 0, 0, 2)
for i in range(R): e.step(0, *stick_for(0, 80), 2)
for i in range(D): e.step(0, *stick_for(90, 80), 2)
for i in range(80):
    e.step(0, *stick_for(180, 80), 2)
    if player(e)['x'] < 14: break
for i in range(W): e.step(0, 0, 0, 2)
up, dn = stick_for(270, 30), stick_for(90, 30)
for f in range(160):
    if (e.u32(IDX) + 1) % 40 == e.u32(PTR): break
    e.step(0, *(up if f % 2 == 0 else dn), 2)
for i in range(10): e.step(0, 0, 0, 2)
p, l = player(e), laki(); ptr = e.u32(PTR)
full = (e.u32(IDX) + 1) % 40 == ptr
print('M (%.1f, %.1f) L (%.1f, %.1f, %.1f) state %d ptr %d full %s target (%.1f, %.1f)' % (p['x'], p['z'], l['x'], l['y'], l['z'], e.u32(STATE) >> 16, ptr, full, e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)))
if full and (e.u32(STATE) >> 16) == 5 and l['x'] > p['x']:
    e.step(0, 0, 0, 2); e.save(OUT); print('saved', OUT)
