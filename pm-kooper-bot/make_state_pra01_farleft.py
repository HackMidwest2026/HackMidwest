"""pra_01 reflected side, push start at the FAR LEFT (so Lakilester's stale target and the oldest history entries
are as far as possible from the stair strip): from states/pra01_top_start.st (Mario (519, -100)) walk right R frames
and up/down to lane Z, then walk left back to the left edge so Lakilester trails on Mario's right facing left; stop
and wait for follow state 5. Keeps the first variant with pointer not 0 or 39. Saves states/pra01_farleft_<Z>.st.
usage: make_state_pra01_farleft.py Z"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
HIST, IDX, PTR, STATE = 0x8010CEF8, 0x8010D178, 0x8010D188 - 0xC, 0x8010D188
PTR = 0x8010D17C
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/mkfl')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
Z = float(sys.argv[1])
for R in range(20, 60, 3):
    e.load('states/pra01_top_start.st')
    for i in range(R): e.step(0, *stick_for(0, 80), 2)
    for i in range(80):
        p = player(e)
        if abs(p['z'] - Z) < 3: break
        e.step(0, *stick_for(90 if Z > p['z'] else 270, 80), 2)
    for i in range(120):
        e.step(0, *stick_for(180, 80), 2)
        if player(e)['x'] < 512: break
    for i in range(60): e.step(0, 0, 0, 2)
    p, l = player(e), laki(); ptr = e.u32(PTR)
    print(R, 'mario %.1f %.1f laki %.1f %.1f st %d idx %d ptr %d tgt (%.1f, %.1f)' % (p['x'], p['z'], l['x'], l['z'], e.u32(STATE) >> 16, e.u32(IDX), ptr, e.f32(HIST + 16 * ptr + 4), e.f32(HIST + 16 * ptr + 12)))
    if ptr not in (0, 39) and (e.u32(STATE) >> 16) == 5 and l['x'] > p['x'] + 20:
        e.save('states/pra01_farleft_%d.st' % int(-Z)); print('saved'); break
