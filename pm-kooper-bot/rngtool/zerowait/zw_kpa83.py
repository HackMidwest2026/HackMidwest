"""kpa_83 Jr. Troopa pre-battle scene with B held (DIAGNOSTIC setup: GB_KPA83_BowserDoorState set back to 0 and the
room re-entered through a redirected exit, from states/kpa83_e1_s95.st). Per seed: frames to the battle and RNG steps
beyond the per-frame step and the coin. usage: python3 zw_kpa83.py N"""
import os, sys, random
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
from emu import *; from pm import *; from rngsim import *
N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
MAPS = ['kpa_01','kpa_03','kpa_04','kpa_08','kpa_09','kpa_10','kpa_11','kpa_12','kpa_13','kpa_14','kpa_15','kpa_16','kpa_17','kpa_32','kpa_33','kpa_40','kpa_41','kpa_50','kpa_51','kpa_52','kpa_53','kpa_60','kpa_61','kpa_62','kpa_63','kpa_70','kpa_81','kpa_82','kpa_83']
e = Emu('pm-jp.z64', '/dev/shm/pmbot/zw83')
for i in range(60): e.step(0, 0, 0, 2)
e.load('states/kpa83_e1_s95.st'); e.step(0, 0, 0, 2)
e.w8(STORY + 0x12C, 0)                                            # DIAGNOSTIC: Jr. Troopa scene not done yet
yaw = player(e)['yaw']; dx = -70 if yaw < 180 else 70             # walk back out the way Mario came in
red = False
for f in range(600):
    e.step(0, dx, 0, 2); m = e.s16(GAME_MODE)
    if m == GM_CHANGE_MAP and not red:
        g = game_status(e); e.w16(g + 0x86, 22); e.w16(g + 0x8C, MAPS.index('kpa_83')); e.w16(g + 0x8E, 1); red = True   # DIAGNOSTIC: back into kpa_83
    if red and m == GM_WORLD: break
print('entered', where(e), 'after', f, 'frames; redirected', red)
e.save('/dev/shm/pmbot/zw83_in.st'); rnd = random.Random(3)
for n in range(N):
    e.load('/dev/shm/pmbot/zw83_in.st'); e.step(0, 0, 0, 2)
    s = rnd.getrandbits(32); e.w32(SEED, s)                         # DIAGNOSTIC: random seed
    extra = 0; odd = []
    for f in range(4000):
        prev = e.u32(SEED); e.step(B, 0, 0, 2); cur = e.u32(SEED)
        k = 0; t = prev
        while t != cur and k < 20000: t = adv(t); k += 1
        if k not in (1, 2): extra += k - 1; odd.append((f, k))
        if e.s16(GAME_MODE) not in (GM_WORLD, GM_CHANGE_MAP, GM_ENTER_WORLD): break
    print('%08x frames %d mode %d extra steps %d odd frames %d' % (s, f, e.s16(GAME_MODE), extra, len(odd)), odd[:6], flush=True)
