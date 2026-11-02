"""Power on (cold boot) and log gRandSeed every game frame (2 VIs) through the logos, title, file select and file load.
Reports the seed at init (main.c: gRandSeed = 1 + osGetCount()), RNG steps per frame by game mode, and the frame control starts.
No RAM writes. usage: python3 boot_seed.py T0_ [PERIOD] [SAVEDIR]
  A is pressed every PERIOD frames (default 20) from frame T0_ on (the title and file select ignore earlier presses)."""
import os, sys, json, shutil
from collections import Counter
T0_ = int(sys.argv[1]) if len(sys.argv) > 1 else 0
PER = int(sys.argv[2]) if len(sys.argv) > 2 else 20
SAVEDIR_ = sys.argv[3] if len(sys.argv) > 3 else '/tmp/claude-0/pm/savegame'
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
from emu import *; from pm import *; from rngsim import SEED, adv
dd = '/dev/shm/pmbot/rs%d' % os.getpid(); os.makedirs(dd, exist_ok=True)
for f in os.listdir(SAVEDIR_): shutil.copy(os.path.join(SAVEDIR_, f), dd)
e = Emu('pm-jp.z64', dd)
def nsteps(a, b, lim=200000):
    k = 0
    while a != b and k < lim: a = adv(a); k += 1
    return k if a == b else -1
log = []; prev = e.u32(SEED); init = None; mp = None; ctrl = None
print('frame0 seed %08x count %08x' % (prev, e.count()))
for f in range(3000):
    b = A if f >= T0_ and (f - T0_) % PER == 0 and ctrl is None else 0
    e.step(b, 0, 0, 2)
    s = e.u32(SEED); m = e.s16(GAME_MODE)
    if init is None and prev == 1 and s != 1:
        init = {'frame': f, 'seed': s, 'count_now': e.count()}; k = None
    else:
        k = nsteps(prev, s) if init else 0
    log.append((f, m, k, b))
    if m != mp: print('f', f, 'mode', m, 'seed %08x' % s, flush=True); mp = m
    prev = s
    if m == 4 and ctrl is None:
        ctrl = f; print('field mode at f', f, where(e))
    if ctrl is not None and f > ctrl + 120: break
if init: print('INIT f', init['frame'], 'seed %08x' % init['seed'], '=> osGetCount at init %08x' % (init['seed'] - 1))
by = {}
for f, m, k, b in log: by.setdefault(m, Counter())[k] += 1
for m in by: print('mode', m, dict(by[m]))
# seed at control as steps from init
K = sum(k for f, m, k, b in log if k and f <= ctrl)
print('RESULT start', T0_, 'per', PER, 'ctrl_frame', ctrl, 'steps_init_to_ctrl', K, 'extra', K - (ctrl - init['frame']))
K2 = sum(k for f, m, k, b in log if k)
print('RESULT2 steps to end', K2, 'end frame', log[-1][0], 'extra', K2 - (log[-1][0] - init['frame']), 'seed_end %08x' % e.u32(SEED))
json.dump({'init': init, 'ctrl': ctrl, 'log': log, 'start': T0_, 'per': PER}, open('/dev/shm/pmbot/boot_%d_%d.json' % (T0_, PER), 'w'))
