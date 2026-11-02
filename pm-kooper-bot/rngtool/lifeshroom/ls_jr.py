"""Jr. Troopa fight, played without the page: is Mario's death RNG, and what does the Life Shroom revive do to the RNG?
Plays the route's T1-T3 (sr_fight.py's inputs, with human delays instead of beeps) from states/boss_0207_route_menu.st
and logs every game frame: battle state, RNG steps that frame, every rand_int call (max, value, caller) and Mario's HP.
DIAGNOSTIC: the fight's starting seed is set to a random value (an unknown run).
usage: M64P_DBG=1 python3 ls_jr.py OUTDIR N [SEED0hex]   (N fights)"""
import os, sys, json, random
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *; from pm import *; from btl import *; from rngsim import *
OUT = os.path.abspath(sys.argv[1]); os.makedirs(OUT, exist_ok=True); N = int(sys.argv[2])
rnd = random.Random(int(sys.argv[3], 16) if len(sys.argv) > 3 else 1)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ls%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
F = []; S = [0]; MARK = []
def hpd(): return (e.s8(PLAYER_DATA + 2), e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8))
def step(b=0, x=0, y=0):
    prev = e.u32(SEED); e.step(b, x, y, 2); cur = e.u32(SEED)
    k = 0; t = prev
    while t != cur and k < 5000: t = adv(t); k += 1
    calls = []
    for ev in e.dbg_events():
        mx = ev['a0'] if ev['a0'] < 0x80000000 else ev['a0'] - (1 << 32)
        S[0], v = rand_int(S[0], mx); calls.append([mx, v, ev['ra']])
    S[0] = cur
    F.append([len(F), bstate(e), k, calls, *hpd(), b])
def jw(n, b=0, x=0, y=0):
    for i in range(n): step(b if i == 0 else 0, x, y if i == 0 else 0)
def until(states, cap=3000, mash=False):
    for f in range(cap):
        if bstate(e) in states: return f
        step(A if (mash and f % 2 == 0) else 0)
    raise RuntimeError('state %d' % bstate(e))
def mark(s): MARK.append([len(F), s])
def conf(fast=None): jw(fast if fast is not None else rnd.randint(6, 20)); step(A)
def fight(seed):
    F.clear(); MARK.clear()
    e.load('states/boss_0207_route_menu.st'); e.step(0, 0, 0, 2)
    e.w32(SEED, seed); e.w32(SEED2, seed); S[0] = seed           # DIAGNOSTIC: unknown starting seed
    until([13]); jw(rnd.randint(20, 60)); mark('T1')
    jw(15, A); jw(10, 0, 0, -70); jw(10, 0, 0, -70); jw(20, A); until([17], cap=80); conf()
    until([14]); jw(10)
    jw(25, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); conf()
    until([13, 14, 27, 32], mash=True); until([13], cap=4000); mark('T2')
    jw(rnd.randint(30, 300))
    jw(30, Z); jw(25, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); conf()
    until([13], cap=4000, mash=True); jw(15)
    jw(15, 0, 0, 70); jw(25, A); step(A)
    for i in range(60):
        if bstate(e) == 17: break
        step()
    conf(2); until([13], cap=4000); jw(20); mark('T3')
    jw(12, 0, 0, -70); jw(22, A); jw(10, 0, 0, -70); jw(10, 0, 0, -70); jw(20, A); until([17], cap=80); conf()
    until([14]); jw(10)
    jw(25, A); jw(10, 0, 0, -70); jw(25, A); until([17], cap=80); mark('T3bomb'); conf()
    h0 = hpd(); mark('T3enemy')
    # through Jr. Troopa's turn (and a revive if Mario dies) to the next menu, mashing nothing
    until([13, 14, 27, 32], cap=4000)
    for i in range(3000):
        if bstate(e) == 13 and F[-1][4] > 0: break
        step()
    mark('T4menu')
    return h0
for n in range(N):
    seed = rnd.getrandbits(32)
    try: h0 = fight(seed)
    except Exception as ex: print('seed %08x error %s' % (seed, ex), flush=True); continue
    died = any(f[4] <= 0 for f in F)
    print('seed %08x T3 hp_before %s died %s end hp %s frames %d' % (seed, h0, died, F[-1][4:6], len(F)), flush=True)
    json.dump({'seed': seed, 'frames': F, 'marks': MARK, 'died': died}, open('%s/jr_%08x.json' % (OUT, seed), 'w'))
