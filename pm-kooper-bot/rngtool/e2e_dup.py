"""End-to-end test of the Duplighost profile in the emulator (4 Duplighosts, Bombette out; DIAGNOSTIC: the starting
seed is set to a random value to stand in for an unknown run).
 1. Mario's turn-1 menu: idle ~45 s; every coin shine becomes a tap at (shine visible) + reaction (200 +- 30 ms).
 2. The tool finds the seed from the taps alone.
 3. Mario: Strategies > do nothing (random waits). Bombette: Strategies, hand on do nothing. Idle ~10 s more (taps):
    the tool resyncs.
 4. The tool plans the confirm (dup4 profile, first run of >= 2 working frames >= 2 s ahead); the emulator presses A on
    the planned frame. Success = all four RandInt(1000) copy rolls < 600 (debug core).
usage: M64P_DBG=1 e2e_dup.py SEED"""
import sys, os, json, random, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emu import *
from pm import *
from btl import *
from rngsim import *
HERE = os.path.dirname(os.path.abspath(__file__))
FRAME_MS = 1000 / (60000 / 1001 / 2)
SH = 700 * (0xFFFFFFFF // 1010)
seed0 = int(sys.argv[1], 16); rnd = random.Random(seed0)
def tool(cmd, arg):
    r = subprocess.run(['node', os.path.join(HERE, 'tool_cli.js'), cmd, json.dumps(arg)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/e2ed%d' % os.getpid())
e.load('states/boss_2402_bomb_menu.st'); e.step(0, 0, 0, 2)
e.w32(SEED, seed0); e.w32(SEED2, seed0)                    # DIAGNOSTIC: unknown starting seed
F = [0]
def step(b=0, x=0, y=0):
    prev = e.u32(SEED); e.step(b, x, y, 2); F[0] += 1; cur = e.u32(SEED)
    k = 0; t = prev
    while t != cur and k < 5000: t = adv(t); k += 1
    return prev, k
def watch(n):
    taps, sh = [], []
    for i in range(n):
        prev, k = step()
        if k == 2 and adv(prev) >= SH: sh.append(F[0]); taps.append((F[0] + 6) * FRAME_MS + rnd.gauss(200, 30))
    return taps, sh
def wait(n):
    for i in range(n): step()
taps1, sh1 = watch(1350)
r = tool('find', {'taps': taps1}); seeds = r['seeds']; extra = 0
while len(seeds) > 1 and extra < 1800:
    t, s_ = watch(150); taps1 += t; sh1 += s_; extra += 150
    seeds = tool('filter', {'seeds': seeds, 'taps': taps1})['seeds']
print('segment 1: %d shines -> %d seed(s)' % (len(taps1), len(seeds)))
if len(seeds) != 1: print('FAIL: seed'); sys.exit(1)
pat1 = tool('pattern', {'taps': taps1})['pattern']; aft = tool('after', {'seed': seeds[0], 'pattern': pat1})
# Mario: Strategies > do nothing; Bombette: Strategies, hand on do nothing
for b, x, y in [(0, 0, 70), (0, 0, 70), (A, 0, 0), (0, 0, -70), (A, 0, 0)]:
    wait(rnd.randint(10, 20)); step(b, x, y)
wait(40); assert bstate(e) == 14, bstate(e)
for b, x, y in [(0, 0, 70), (A, 0, 0), (0, 0, -70)]:
    wait(rnd.randint(10, 20)); step(b, x, y)
taps2, sh2 = watch(300)
def resync():
    E = (taps2[0] - taps1[-1]) / FRAME_MS
    return tool('resync', {'from': aft['seedAfterLastDraw'], 'taps': taps2, 'nlo': max(0, int(E) - 300), 'nmax': int(E) + 6000})
rs = resync(); extra = 0
while len(rs['matches']) != 1 and extra < 900:
    t, s_ = watch(90); taps2 += t; sh2 += s_; extra += 90; rs = resync()
if len(rs['matches']) != 1: print('FAIL: resync'); sys.exit(1)
bl = tool('beforelast', {'seed': rs['matches'][0]['seed'], 'pattern': rs['pattern']})['seed']
L2 = sh2[-1]; now_rel = F[0] - L2
pl = tool('plan', {'seed': bl, 'from': now_rel + 60, 'to': now_rel + 60 + 1800, 'minRun': 2, 'profile': 'dup4'})
w = pl['window']; print('plan: confirm frames %s (relative to the last shine), now = %d' % (w, now_rel))
if not w: print('FAIL: no window'); sys.exit(1)
target = L2 + w['start'] + (w['length'] - 1) // 2 + 1        # model frame t = step number L2 + t (+1: 1-based F)
wait(target - 1 - F[0]); assert F[0] == target - 1
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
s = e.u32(SEED); rolls = []                         # replay every rand_int call the game makes (debug core log)
step(A)
for i in range(420):
    for x in e.dbg_events():
        mx = x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)
        s, v = rand_int(s, mx)
        if x['ra'] == 0x802D46E0 and mx == 1000: rolls.append(v)
    if len(rolls) >= 4 or (rolls and rolls[-1] >= 600): break
    step()
ok = len(rolls) == 4 and all(v < 600 for v in rolls)
print('RESULT seed %08x: copy rolls %s -> %s (window %d frames)' % (seed0, rolls, 'ALL 4 COPIED' if ok else 'missed', w['length']))
