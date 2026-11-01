# (run from the emulator working dir, bot1/) """kpa_11 as ridden in the route: stand, mount Lakilester (C-down), ride down-left, then left. Frames with RNG step
counts other than 1 (frame) or 2 (frame + coin) = another RNG user."""
import sys
from emu import *
from pm import *
from rngsim import *
st = sys.argv[1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rr3_' + st)
e.load('states/' + st); e.step(0, 0, 0, 2)
odd = []; n = 0; pts = []
for f in range(1500):
    b, x, y = 0, 0, 0
    if f == 120: b = D_CBUTTON
    elif 150 < f < 600: x, y = -50, -50
    elif f >= 600: x = -70
    prev = e.u32(SEED); e.step(b, x, y, 2); cur = e.u32(SEED)
    if e.s16(GAME_MODE) != GM_WORLD: print('  left world mode at', f); break
    k = 0; s = prev
    while s != cur and k < 5000: s = adv(s); k += 1
    n += 1
    if f % 150 == 0: p = player(e); pts.append((f, round(p['x']), round(p['z']), p['action'], where(e)[1]))
    if k not in (1, 2): odd.append((f, k))
print(st, 'frames', n, 'path', pts, '| odd frames:', len(odd), odd[:12])
