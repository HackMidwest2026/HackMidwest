# (run from the emulator working dir, bot1/) """Lava rooms: stand 300 frames, mount Lakilester (C-down), then ride right 900 frames. Frames with RNG step counts
other than 1 (frame) or 2 (frame + coin) = another RNG user in the room."""
import sys
from emu import *
from pm import *
from rngsim import *
st = sys.argv[1]; dx = int(sys.argv[2]) if len(sys.argv) > 2 else 70
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rr2_' + st)
e.load('states/' + st); e.step(0, 0, 0, 2)
odd = []; n = 0; acts = set(); maps = set()
for f in range(1260):
    b, x = 0, 0
    if f == 300: b = D_CBUTTON
    elif f > 330: x = dx
    prev = e.u32(SEED); e.step(b, x, 0, 2); cur = e.u32(SEED)
    if e.s16(GAME_MODE) != GM_WORLD: print('  left world mode at', f); break
    k = 0; s = prev
    while s != cur and k < 5000: s = adv(s); k += 1
    n += 1; acts.add(player(e)['action']); maps.add(where(e))
    if k not in (1, 2): odd.append((f, k))
p = player(e)
print(st, 'maps', sorted(maps), 'frames', n, 'x %.0f' % p['x'], 'actions', sorted(acts), '| odd frames:', len(odd), odd[:10])
