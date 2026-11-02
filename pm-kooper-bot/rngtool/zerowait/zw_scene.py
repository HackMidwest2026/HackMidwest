"""Zero-wait study: RNG use in a scene from a savestate until the next battle or player control.
usage: python3 zw_scene.py STATE NSEEDS [AEVERY] [maxframes]
Per frame: RNG steps; the per-frame step (1) and a coin draw (+1, rand_int(100) uses 1 step) are expected, anything
else is listed. A is pressed every AEVERY frames (message advance); AEVERY=0: random 10-35 frames between presses. Stops when the game mode leaves the world
(battle) or after maxframes. DIAGNOSTIC: a random seed is written at the start (stands for an unknown run)."""
import sys, os, random
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
from rngsim import *
st = sys.argv[1]; N = int(sys.argv[2]); AE = int(sys.argv[3]) if len(sys.argv) > 3 else 20; MAXF = int(sys.argv[4]) if len(sys.argv) > 4 else 3000
e = Emu('pm-jp.z64', '/dev/shm/pmbot/zw_' + os.path.basename(st))
rnd = random.Random(1)
def flag(i): return (e.u32(SAVE + 0xFB0 + 4 * (i // 32)) >> (i % 32)) & 1
for run in range(N):
    e.load('states/' + st); e.step(0, 0, 0, 2)
    sd = rnd.getrandbits(32); e.w32(SEED, sd)                       # DIAGNOSTIC: random seed
    if run == 0: print(st, where(e), 'story', e.s8(STORY), 'GF 0x1FA', flag(0x1FA), 'mode', e.s16(GAME_MODE))
    odd = []; n = 0; extra = 0; ph = rnd.randrange(max(1, AE)); nxt = [rnd.randint(0, 20)]
    for f in range(MAXF):
        if AE > 0: b = A if (f + ph) % AE == 0 else 0
        else:
            b = A if f >= nxt[0] else 0
            if b: nxt[0] = f + rnd.randint(10, 35)
        prev = e.u32(SEED); e.step(b, 0, 0, 2); cur = e.u32(SEED)
        k = 0; s = prev
        while s != cur and k < 20000: s = adv(s); k += 1
        n += 1
        if k not in (1, 2): odd.append((f, k)); extra += k - 1
        m = e.s16(GAME_MODE)
        if m not in (GM_WORLD, GM_CHANGE_MAP, GM_ENTER_WORLD): break
    print('seed %08x frames %d mode %d where %s | odd frames %d extra steps %d' % (sd, n, e.s16(GAME_MODE), where(e), len(odd), extra), odd[:12])
