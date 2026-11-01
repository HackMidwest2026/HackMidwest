"""End-to-end test of the Jr. Troopa profiles in the emulator. From a decisive-point state (the screen where the
deciding confirm is pressed; DIAGNOSTIC: random starting seed), watch the coin ~45 s (taps = shine + 200 +- 30 ms),
find the seed with the tool, plan with the profile, confirm on the planned frame (Bomb: mash the meter; Power Bounce:
press A inside every bounce window), then check the game: Close Call = Mario's HP unchanged after Jr. Troopa's attack;
Power Bounce 6+ = Jr. Troopa at 0 HP after the bounces.
usage: e2e_jr.py PROFILE SEED   (PROFILE: jrcc_bomb, jrcc_syrup, jrcc_nothing, jrpb6)"""
import sys, os, json, random, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emu import *
from pm import *
from btl import *
from rngsim import *
HERE = os.path.dirname(os.path.abspath(__file__))
FRAME_MS = 1000 / (60000 / 1001 / 2)
SH = 700 * (0xFFFFFFFF // 1010)
PROF, seed0 = sys.argv[1], int(sys.argv[2], 16); rnd = random.Random(seed0)
ST = {'jrcc_bomb': 'states/jr_t3_bomb_target.st', 'jrcc_syrup': 'states/jr_t4_syrup.st', 'jrcc_nothing': 'states/jr_t5_nothing.st',
      'jrpb6': 'states/jr_t6_pb_target.st'}[PROF]
ST = os.environ.get('ST', ST)
def tool(cmd, arg):
    r = subprocess.run(['node', os.path.join(HERE, 'tool_cli.js'), cmd, json.dumps(arg)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/e2ej%d' % os.getpid())
e.load(ST); e.step(0, 0, 0, 2)
e.w32(SEED, seed0); e.w32(SEED2, seed0)                    # DIAGNOSTIC: unknown starting seed
F = [0]
def step(b=0):
    prev = e.u32(SEED); e.step(b, 0, 0, 2); F[0] += 1; cur = e.u32(SEED)
    k = 0; t = prev
    while t != cur and k < 5000: t = adv(t); k += 1
    return prev, k
taps, sh = [], []
for i in range(1350):
    prev, k = step()
    if k == 2 and adv(prev) >= SH: sh.append(F[0]); taps.append((F[0] + 6) * FRAME_MS + rnd.gauss(200, 30))
r = tool('find', {'taps': taps}); seeds = r['seeds']
while len(seeds) > 1:
    for i in range(150):
        prev, k = step()
        if k == 2 and adv(prev) >= SH: sh.append(F[0]); taps.append((F[0] + 6) * FRAME_MS + rnd.gauss(200, 30))
    seeds = tool('filter', {'seeds': seeds, 'taps': taps})['seeds']
if len(seeds) != 1: print('FAIL: seed'); sys.exit(1)
pat = tool('pattern', {'taps': taps})['pattern']
bl = tool('beforelast', {'seed': seeds[0], 'pattern': pat})['seed']
L = sh[-1]; now_rel = F[0] - L
pl = tool('plan', {'seed': bl, 'from': now_rel + 60, 'to': now_rel + 60 + 1800, 'minRun': 2, 'profile': PROF})
w = pl['window']
if not w: print('FAIL: no window'); sys.exit(1)
target = L + w['start'] + (w['length'] - 1) // 2   # model frame t = the step numbered L + t
while F[0] < target - 1: step()
hp0, jr = e.s8(PLAYER_DATA + 2), e.u32(BSTATUS + 0xE0)
PB = {47, 74, 102, 130, 158, 186, 214}
for f in range(900):
    if f == 0: b = A
    elif PROF == 'jrcc_bomb': b = A if (10 < f < 200 and f % 2 == 0) else 0
    elif PROF == 'jrpb6': b = A if f in PB else 0
    else: b = 0
    step(b)
    if f > 60 and bstate(e) in (13, 14, 27, 32): break
if PROF == 'jrpb6':
    ok = e.s8(jr + 0x1B8) <= 0; what = 'Jr. Troopa HP %d' % e.s8(jr + 0x1B8)
else:
    ok = e.s8(PLAYER_DATA + 2) == hp0 and bstate(e) in (13, 14); what = 'Mario HP %d -> %d, state %d' % (hp0, e.s8(PLAYER_DATA + 2), bstate(e))
print('RESULT %s seed %08x: window %d frames -> %s (%s)' % (PROF, seed0, w['length'], 'WORKED' if ok else 'missed', what))
