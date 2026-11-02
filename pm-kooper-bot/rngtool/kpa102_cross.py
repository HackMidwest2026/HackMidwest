"""(run from bot1/) kpa_102 crossing (copied as kpa102_cross.py): DIAGNOSTIC seed write, then run right along the corridor; count RNG steps beyond
1/frame + coin draws until the door (kpa_53) or a battle. usage: _k102.py seedhex delay [zigzag]"""
import sys
from emu import *
from pm import *
from rngsim import *
SEEDV, DELAY = int(sys.argv[1], 16), int(sys.argv[2]); ZZ = len(sys.argv) > 3
e = Emu('pm-jp.z64', '/dev/shm/pmbot/k102_%x_%d' % (SEEDV, DELAY))
e.load('states/kpa102_e0.st'); e.step(0, 0, 0, 2)
e.w32(SEED, SEEDV)    # DIAGNOSTIC: start seed
extra = 0; coin = 0; out = 'timeout'
for f in range(900):
    x = 0 if f < DELAY else 80
    yv = int(sys.argv[3]) if ZZ else 0
    b = 0x8000 if (player(e)['x'] > 700 and f % 4 == 0) else 0
    prev = e.u32(SEED); e.step(b, x, yv, 2); cur = e.u32(SEED)
    k = 0; t = prev
    while t != cur and k < 20000: t = adv(t); k += 1
    if e.s16(GAME_MODE) != GM_WORLD: out = 'mode %d at f%d x=%d' % (e.s16(GAME_MODE), f, player(e)['x']); break
    if where(e)[1] != 0 and False: pass
    if k == 2: coin += 1
    elif k != 1: extra += k - 1
print('seed %08x delay %d zz %s: %s | frames %d coin %d extra steps %d' % (SEEDV, DELAY, ZZ, out, f, coin, extra))
