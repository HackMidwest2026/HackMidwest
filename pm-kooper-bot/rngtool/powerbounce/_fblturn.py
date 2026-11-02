"""(run from bot1/) lightning (e00bc194) frames through a whole turn cycle from fb2_t7like_menu.st (DIAGNOSTIC as _fbdie):
Focus, Lakilester ability, Bowser's turn (+ revive), back to the menu, 600 frames idle. Checks both periodic sources."""
import sys, os
from emu import *
from pm import *
from btl import *
from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fbl%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.load('states/fb2_t7like_menu.st'); e.step(0, 0, 0, 2)
e.w16(PLAYER_DATA + 0x1B4, 0x95); e.w8(PLAYER_DATA + 2, 1); e.w32(SEED, 0x73cf256d)    # DIAGNOSTIC
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
seq = [(128, 0, 30), (128, 0, 200), (0, 0, 30), (0, 70, 20), (0, 70, 20), (128, 0, 30), (128, 0, 30), (128, 0, 30), (0, 0, 2400)]
f = 0; L = []; st = []
for b, x, n in seq:
    for k in range(n):
        e.step(b if k == 0 else 0, x if k == 0 else 0, 0, 2)
        for ev in e.dbg_events():
            if ev['ra'] == 0xE00BC194: L.append(f)
        s = bstate(e)
        if not st or st[-1][1] != s: st.append((f, s))
        f += 1
A1 = [78, 83, 113, 118]; A2 = [18, 78, 88, 178]
pred = [g for g in range(f) for _ in range(((g % 130) in A1) + ((g % 220) in A2))]
print('states', st); print('n', len(L), 'pred', len(pred)); print('match', L == pred)
print('diff', sorted(set(L) ^ set(pred))[:30])
