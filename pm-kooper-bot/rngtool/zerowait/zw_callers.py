"""Callers of rand_int during a scene (debug core). usage: M64P_DBG=1 python3 zw_callers.py STATE AEVERY [maxframes]
DIAGNOSTIC: random seed written at the start."""
import os, sys, random, collections
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
from emu import *; from pm import *; from btl import *; from rngsim import *
st = sys.argv[1]; AE = int(sys.argv[2]); MAXF = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
e = Emu('pm-jp.z64', '/dev/shm/pmbot/zc%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1)
e.load('states/' + st); e.step(0, 0, 0, 2); e.dbg_events()
s = random.getrandbits(32); e.w32(SEED, s); e.w32(SEED2, s)        # DIAGNOSTIC
byf = []
for f in range(MAXF):
    e.step(B if AE < 0 else (A if f % AE == 3 else 0), 0, 0, 2)
    ev = [x for x in e.dbg_events() if x['ra'] not in (0x800269ac, 0x80146d54)]
    if ev: print(f, dict(collections.Counter((hex(x['ra']), x['a0']) for x in ev)), flush=True)
    if e.s16(GAME_MODE) not in (GM_WORLD, GM_CHANGE_MAP, GM_ENTER_WORLD): break
print('frames', f)
