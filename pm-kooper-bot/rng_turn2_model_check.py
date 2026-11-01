"""Turn-2 menu (after Super Jump Charge + Spiny Flip + Bowser's attack): idle RNG check, then Time Out success for
target-confirm delays D0..D1-1 in the emulator vs the model (rngtool/timeout_model.py)."""
import sys, os, collections
sys.path.insert(0, 'rngtool')
from emu import *
from pm import *
from btl import *
from rngsim import *
import timeout_model as TM
seed = int(sys.argv[1], 16); D0, D1 = int(sys.argv[2]), int(sys.argv[3])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/t2w%d' % os.getpid())
ST = 'states/boss_2302_turn2.st'
def start():
    e.load(ST); e.step(0, 0, 0, 2); e.w32(SEED, seed); e.w32(SEED2, seed)      # DIAGNOSTIC: chosen seed
# 1) idle: steps per frame, coin frames (for the model's coin phase)
start(); ks = []; prev = e.u32(SEED)
for i in range(300):
    e.step(0, 0, 0, 2); cur = e.u32(SEED); k = 0; x = prev
    while x != cur and k < 1000: x = adv(x); k += 1
    ks.append(k); prev = cur
print('idle steps per frame:', sorted(collections.Counter(ks).items()), 'coin frames:', [i for i, k in enumerate(ks) if k == 2][:6])
first_coin = next(i for i, k in enumerate(ks) if k == 2)
# 2) Time Out: menu path down 2, A, up 3, A, then target A at frame 40 + d
MENU = {5: (0, 0, -70), 13: (0, 0, -70), 21: (A, 0, 0), 31: (0, 0, 70), 37: (0, 0, 70), 43: (0, 0, 70), 51: (A, 0, 0)}
def bowser():
    a = e.u32(BSTATUS + 0xE0); return a if 0x80000000 < a < 0x80800000 else None
emu, mod = [], []
for d in range(D0, D1):
    C = 60 + d
    start(); ok = False
    for i in range(C + 420):
        b, x, y = MENU.get(i, (0, 0, 0))
        if i in (C, C + 1): b = A
        e.step(b, x, y, 2)
        a = bowser()
        if a and e.s8(a + 0x210) == 8: ok = True; break
    emu.append('S' if ok else '.')
    mod.append('S' if TM.works(seed, first_coin, C) else '.')
print('emulator %08x: %s' % (seed, ''.join(emu)))
print('model    %08x: %s' % (seed, ''.join(mod)))
