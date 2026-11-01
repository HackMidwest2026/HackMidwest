# (run from the emulator working dir, bot1/) import sys
from emu import *
from pm import *
from rngsim import *
st = sys.argv[1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rs_' + st)
e.load('states/' + st); e.step(0, 0, 0, 2)
yaw = player(e)['yaw']; dx = 70 if yaw < 180 else -70
# expected per game frame: 1 step, plus 1 on coin frames (every 24 or 48 frames). Anything else = another RNG user.
odd = []; n = 0
for f in range(1200):
    x0 = 0 if f < 600 else (dx if (f // 90) % 2 == 0 else -dx)
    prev = e.u32(SEED); e.step(0, x0, 0, 2); cur = e.u32(SEED)
    if e.s16(GAME_MODE) != GM_WORLD: break
    k = 0; s = prev
    while s != cur and k < 5000: s = adv(s); k += 1
    n += 1
    if k == 2:                                         # coin draw? (rand_int(100) uses internal(1009): 1 step)
        continue
    if k != 1: odd.append((f, k))
print(st, where(e), 'frames', n, '| frames with unexpected step counts:', len(odd), odd[:8])
