"""(run from bot1/) per-frame counts of one effect's draws (RA hex) idling in STATE, for a written seed (DIAGNOSTIC).
usage: M64P_DBG=1 _fbfx.py STATE RA SEED N"""
import sys, os
from emu import *
from pm import *
from rngsim import *
st, ra, seed, N = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16), int(sys.argv[4])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fx%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.load('states/' + st); e.step(0, 0, 0, 2); e.w32(SEED, seed); e.w32(SEED2, seed)   # DIAGNOSTIC
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
out = []
for f in range(N):
    e.step(0, 0, 0, 2)
    out.append(sum(1 for x in e.dbg_events() if x['ra'] == ra))
print(''.join(str(min(c, 9)) for c in out))
