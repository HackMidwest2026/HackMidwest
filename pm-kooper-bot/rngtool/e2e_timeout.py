"""End-to-end test of the Time Out RNG tool in the emulator (Hallway Bowser, run-like setup, real inputs from the
first menu on; DIAGNOSTIC: the starting seed is set to a random value to stand in for an unknown run).
 1. Turn-1 menu: idle ~45 s. Every coin shine becomes a "tap" at (shine visible) + reaction time (200 +- 30 ms).
 2. The tool finds the seed from those taps alone (tool_cli.js find).
 3. Turn 1 as in the run (Super Jump Charge, Spiny Flip), with random extra waits; Bowser's turn (hold B).
 4. Turn-2 menu: idle ~15 s more taps; the tool resyncs from the step-1 seed (n search).
 5. The tool plans the target-confirm window (first run of >= 3 working frames >= 2 s ahead); the emulator does the
    menu path (down 2, A, up 3, A) and presses A on the planned frame. Success = Bowser gets STOP.
usage: e2e_timeout.py SEED [SEG1_FRAMES SEG2_FRAMES]"""
import sys, os, json, random, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emu import *
from pm import *
from btl import *
from rngsim import *
HERE = os.path.dirname(os.path.abspath(__file__))
FRAME_MS = 1000 / (60000 / 1001 / 2)
SH = 700 * (0xFFFFFFFF // 1010)
seed0 = int(sys.argv[1], 16); SEG1 = int(sys.argv[2]) if len(sys.argv) > 2 else 1350; SEG2 = int(sys.argv[3]) if len(sys.argv) > 3 else 450
rnd = random.Random(seed0)
def tool(cmd, arg):
    r = subprocess.run(['node', os.path.join(HERE, 'tool_cli.js'), cmd, json.dumps(arg)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/e2e%d' % os.getpid())
e.load('states/boss_2302_run_menu.st'); e.step(0, 0, 0, 2)
e.w32(SEED, seed0); e.w32(SEED2, seed0)                    # DIAGNOSTIC: unknown starting seed
F = [0]
def step(b=0, x=0, y=0):
    """one frame; returns (shine?, draw happened?) for the status-bar coin on this frame"""
    prev = e.u32(SEED); e.step(b, x, y, 2); F[0] += 1; cur = e.u32(SEED)
    k = 0; t = prev
    while t != cur and k < 5000: t = adv(t); k += 1
    return k
def watch(n):
    """idle n frames in a menu; returns (taps ms, draw frames of shines, all draw frames)"""
    taps, shine_frames, draws = [], [], []
    for i in range(n):
        prev = e.u32(SEED); k = step()
        if k == 2:                                # coin draw (first draw of the frame), then the frame step
            draws.append(F[0]); sh = adv(prev) >= SH
            if sh: shine_frames.append(F[0]); taps.append((F[0] + 6) * FRAME_MS + rnd.gauss(200, 30))
        elif k != 1: print('unexpected %d steps on frame %d' % (k, F[0]))
    return taps, shine_frames, draws
# 1-2: find the seed
taps1, sh1, _ = watch(SEG1)
r = tool('find', {'taps': taps1}); seeds = r['seeds']; extra = 0
print('segment 1: %d shines tapped, pattern %d draws, snap residual %.1f frames, search %.1f s -> %d seed(s)' % (len(taps1), len(r['pattern']), r['worst'], r['seconds'], len(seeds)))
while len(seeds) > 1 and extra < 1800:           # keep watching; filter the candidates (instant)
    t, s_, _ = watch(150); taps1 += t; sh1 += s_; extra += 150
    f = tool('filter', {'seeds': seeds, 'taps': taps1}); seeds = f['seeds']
    print('  +%d frames: %d shines, %d candidate(s)' % (extra, len(taps1), len(seeds)))
if len(seeds) != 1: print('FAIL: seed not unique'); sys.exit(1)
seed1 = seeds[0]; pat1 = tool('pattern', {'taps': taps1})['pattern']; aft = tool('after', {'seed': seed1, 'pattern': pat1})
# 3: turn 1 like the run, with random waits
def wait(n):
    for i in range(n): step()
wait(rnd.randint(5, 40)); step(A); wait(rnd.randint(15, 30)); step(0, 0, -70); wait(rnd.randint(8, 20)); step(A); wait(rnd.randint(15, 30)); step(A)
for i in range(4000):
    b = bstate(e)
    if b == 14:
        wait(rnd.randint(10, 40)); step(A); wait(rnd.randint(15, 30)); step(A); wait(rnd.randint(15, 30)); step(A); wait(10)
        for j in range(120): step(A if j % 4 == 0 else 0)
    elif b == 17: wait(rnd.randint(5, 20)); step(A)
    elif b == 13 and i > 100: break
    else: step(B)
wait(rnd.randint(20, 60))
print('turn 2 menu reached at frame', F[0], 'state', bstate(e), 'Mario HP', e.s8(PLAYER_DATA + 2))
# 4: resync
taps2, sh2, draws2 = watch(SEG2)
NLO, NHI = int(os.environ.get('NLO', -200)), int(os.environ.get('NHI', 6000))
def do_resync():
    E = (taps2[0] - taps1[-1]) / FRAME_MS        # elapsed frames between the two taps (reaction noise cancels mostly)
    return E, tool('resync', {'from': aft['seedAfterLastDraw'], 'taps': taps2, 'nlo': int(E) + NLO, 'nmax': int(E) + NHI})
E, rs = do_resync(); extra = 0
while len(rs['matches']) != 1 and extra < 1800:
    t, s_, d_ = watch(90); taps2 += t; sh2 += s_; extra += 90
    E, rs = do_resync()
print('segment 2: %d shines over %d+%d frames, %d match(es); n - E for matches: %s' % (len(taps2), SEG2, extra, len(rs['matches']), [round(m['n'] - E) for m in rs['matches']]))
if len(rs['matches']) != 1: print('FAIL: resync not unique'); sys.exit(1)
bl = tool('beforelast', {'seed': rs['matches'][0]['seed'], 'pattern': rs['pattern']})['seed']
L2 = sh2[-1]                                   # frame of the last tapped shine's draw (frame 0 of the plan)
now_rel = F[0] - L2
pl = tool('plan', {'seed': bl, 'from': now_rel + 60, 'to': now_rel + 60 + 900, 'minRun': 3})
w = pl['window']; print('plan: confirm frames %s (relative to the last shine), now = %d' % (w, now_rel))
if not w: print('FAIL: no window'); sys.exit(1)
# model frame t = the (L2 + t)-th emulator step (F counts steps from 1; the shine draw happened on step L2)
target = L2 + w['start'] + 1                    # aim one frame into the window
# 5: menu path then confirm on the target frame
wait(target - 61 - F[0])
MENU = {5: (0, 0, -70), 13: (0, 0, -70), 21: (A, 0, 0), 31: (0, 0, 70), 37: (0, 0, 70), 43: (0, 0, 70), 51: (A, 0, 0)}
for i in range(60): step(*MENU.get(i, (0, 0, 0)))
assert F[0] == target - 1
step(A); step(A)                                 # the confirm press: first frame = step number `target`
ok = False
for i in range(420):
    step()
    a = e.u32(BSTATUS + 0xE0)
    if 0x80000000 < a < 0x80800000 and e.s8(a + 0x210) == 8: ok = True; break
print('RESULT seed %08x: Time Out %s (window %d frames)' % (seed0, 'WORKED' if ok else 'missed', w['length']))
if os.environ.get('DUMP'):
    json.dump({'taps1': taps1, 'taps2': taps2, 'seed1': seed1, 'seed2': rs['matches'][0]['seed'], 'window': w, 'ok': ok}, open(os.environ['DUMP'], 'w'))
