"""(run from bot1/) Blooper idle draws: from a state, step N frames without input, count rand_int callers. DIAGNOSTIC: none."""
import sys, os, collections
from emu import *
from pm import *
from btl import *
from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/bli%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT)
st, N = sys.argv[1], int(sys.argv[2])
e.load(st); e.step(0, 0, 0, 2); e.dbg_log(1); e.dbg_events()
cnt = collections.Counter(); frames = collections.defaultdict(list)
for f in range(N):
    e.step(0, 0, 0, 2)
    for x in e.dbg_events():
        cnt[hex(x['ra'])] += 1
        if x['ra'] != 0x800269AC: frames[hex(x['ra'])].append(f)
print('bstate', bstate(e), dict(cnt))
for k, v in frames.items(): print(k, len(v), v[:12], 'gaps', sorted(set(b - a for a, b in zip(v, v[1:])))[:10])
