"""(run from bot1/) Library (kkj_16) item pickups: DIAGNOSTIC setup teleports Mario onto the item, then counts RNG steps
per frame (expected 1, or 2 on coin frames) while the item-get message shows and is closed with A."""
import sys, struct
from emu import *
from pm import *
from rngsim import *
X, Y, Z = map(float, sys.argv[1:4])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/pk_%d' % int(X))
e.load('states/kkj16_e0_s95.st'); e.step(0, 0, 0, 2)
fb = lambda v: struct.unpack('>I', struct.pack('>f', v))[0]
for k, v in enumerate((X, Y + 2, Z)): e.w32(PLAYER + PS_POS + 4 * k, fb(v))   # DIAGNOSTIC setup: teleport
odd = []; log = []
for f in range(700):
    btn = 0x8000 if (f >= 200 and f % 40 == 0) else 0   # A every 40 frames after 200 (close the message)
    prev = e.u32(SEED); e.step(btn, 0, 0, 2); cur = e.u32(SEED)
    k = 0; s = prev
    while s != cur and k < 5000: s = adv(s); k += 1
    if k not in (1, 2): odd.append((f, k))
    if f % 50 == 0: log.append((f, e.s16(GAME_MODE), round(player(e)['x']), round(player(e)['y'])))
inv = [e.u16(PLAYER_DATA + 0x1B4 + 2 * i) for i in range(10)]
print('pos', (X, Y, Z), 'odd', len(odd), odd[:12]); print(log); print('items', inv)
import re
for nm in ('GF_KKJ16_Item_LifeShroom','GF_KKJ16_Item_PowerRush'):
    n=int(re.search(nm+r'\s*=\s*GameFlag\((0x[0-9A-F]+)\)',open('../papermario/include/saved_flag_names.h').read()).group(1),16)
    print(nm, 'set' if e.u32(SAVE+0x0FB0+4*(n//32))>>(n%32)&1 else 'not set')
