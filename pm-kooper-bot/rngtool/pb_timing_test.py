"""Power Bounce action-command timing test (Hallway Bowser, DIAGNOSTIC fixed seed).
 1. Map each bounce's AC window (single A press at frame p after the target confirm; success = the bounce's
    rand_int(100) cap roll, ra 0x802A1168, shows up).
 2. For every bounce, press on every frame of its window (others at the window start) and compare the roll list,
    the frame the move ends and the seed at the end.
Result (seed 12345678, JP): windows after the confirm A at 42-47, 68-73, 95-99, 122-125, 149-151 (6/6/5/4/3 frames);
rolls on confirm+73, +99, +125, +151, +177 (every 26 frames) = 35, 47, 22, 31, 79 -> capped at 6 hits (79 > 22).
All 34 timing variants (every window frame of every bounce, plus 10 random mixes) gave the same rolls, end frame
and final seed: press timing inside the window does not touch the RNG; the chain is fixed by the confirm frame.
A press before the window (e.g. 4-14 frames early) loses the bounce (normal early-press lockout).
Needs the debug core (M64P_DBG=1) and states/boss_2302_pb_menu.st (Hallway Bowser, Power Bounce equipped).
usage: pb_timing_test.py SEED"""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emu import *
from pm import *
from btl import *
from rngsim import *
ROLL_RA = 0x802A1168
seed = int(sys.argv[1], 16)
D = '/dev/shm/pmbot/pbc%d' % os.getpid(); os.makedirs(D, exist_ok=True)
e = Emu('pm-jp.z64', D)
e.load('states/boss_2302_pb_menu.st'); e.step(0,0,0,2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
def w(n):
    for i in range(n): e.step(0,0,0,2)
w(10); e.step(A,0,0,2); w(15); e.step(0,0,-70,2); w(8); e.step(A,0,0,2); w(20)
assert bstate(e) == 17
e.bp_add(RAND_INT); e.dbg_log(1)
S0 = D + '/s0.st'; e.save(S0)
def run(presses, stop_after_rolls=None, save_at=None):
    """from the target screen; A on frame 0 (confirm) and on each press frame. Returns (rolls [(frame, value, chance?)],
    end frame, final seed). stop_after_rolls: stop as soon as that many rolls happened."""
    e.load(S0); e.dbg_events(); s = e.u32(SEED); rolls = []; ps = set(presses) | {0}
    for f in range(1500):
        if save_at is not None and f == save_at: e.save(D + '/mid.st')
        e.step(A if f in ps else 0, 0, 0, 2)
        for x in e.dbg_events():
            mx = x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)
            s, v = rand_int(s, mx)
            if x['ra'] == ROLL_RA: rolls.append((f, v))
        if stop_after_rolls is not None and len(rolls) >= stop_after_rolls: return rolls, None, None
        if bstate(e) not in (17, 18, 19) and f > 30: return rolls, f, e.u32(SEED)
    return rolls, None, e.u32(SEED)
# 1: windows, greedy (earliest working frame for each bounce)
windows = []; presses = []; lo = 1
while True:
    ok = []
    for p in range(lo, lo + 90):
        r, end, _ = run(presses + [p], stop_after_rolls=len(presses) + 1)
        if end is None and len(r) == len(presses) + 1: ok.append(p)
        elif ok: break
    if not ok: break
    windows.append((ok[0], ok[-1])); presses.append(ok[0]); lo = ok[-1] + 1
    print('bounce %d: window frames %d-%d (%d frames)' % (len(windows), ok[0], ok[-1], len(ok)), flush=True)
base = run(presses); print('earliest presses', presses, '->', 'rolls', base[0], 'end', base[1], 'seed %08x' % base[2], flush=True)
# 2: vary each bounce over its window
diff = 0; n = 0
for k, (a, b) in enumerate(windows):
    for p in range(a, b + 1):
        pr = list(presses); pr[k] = p; r = run(pr); n += 1
        same = r == base
        if not same: diff += 1; print('  bounce %d press %d: DIFFERENT rolls %s end %s seed %08x' % (k + 1, p, r[0], r[1], r[2]))
    print('bounce %d: pressed on each of %d window frames' % (k + 1, b - a + 1), flush=True)
# also: all bounces at the window end, and a random mix
import random
rnd = random.Random(1)
for t in range(10):
    pr = [rnd.randint(a, b) for a, b in windows]; r = run(pr); n += 1
    if r != base: diff += 1; print('  mix %s: DIFFERENT %s' % (pr, r))
print('RESULT seed %08x: %d bounces, %d timing variants, %d differed' % (seed, len(windows), n, diff))
