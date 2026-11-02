"""Hallway Bowser battle start -> T1 menu (states/boss_2302_route_start.st, a DIAGNOSTIC battle start): per seed, frames
and RNG steps (A every 20 frames for the messages) to the first menu and the extra draws. DIAGNOSTIC: random seed written at the start.
usage: M64P_DBG=1 python3 ls_hwintro.py N"""
import os, sys, random, collections
N = int(sys.argv[1])
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
from emu import *; from pm import *; from btl import *; from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/lh%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT); e.dbg_log(1); rnd = random.Random(5)
for n in range(N):
    e.load('states/boss_2302_route_start.st'); e.step(0, 0, 0, 2); e.dbg_events()
    s = rnd.getrandbits(32); e.w32(SEED, s); e.w32(SEED2, s)        # DIAGNOSTIC
    st = []; tot = 0; ex = collections.Counter()
    for f in range(3000):
        prev = e.u32(SEED); e.step(A if f % 20 == 10 else 0, 0, 0, 2); cur = e.u32(SEED)
        k = 0; t = prev
        while t != cur and k < 20000: t = adv(t); k += 1
        tot += k
        for x in e.dbg_events():
            if x['ra'] not in (0x800269ac, 0x80146d54): ex[hex(x['ra'])] += 1
        if f % 300 == 0: st.append(bstate(e))
        if bstate(e) == 13: break
    print('%08x menu at frame %d, steps %d (extra over 1/frame %d) extra draws %s %s' % (s, f, tot, tot - f - 1, dict(ex), st), flush=True)
