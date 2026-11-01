"""Jr. Troopa route probe: from states/jr_t1_bomblist.st (Bombette's move list, hand on Bomb) press A (Bomb), A on the
target at frame C, mash A every MASH frames for the meter, then log every non-frame rand_int call until Mario's next
menu. DIAGNOSTIC: seed set. usage: _jrlog.py SEED [MASH]"""
import sys, os, collections
from emu import *
from pm import *
from btl import *
from rngsim import *
seed = int(sys.argv[1], 16); MASH = int(sys.argv[2]) if len(sys.argv) > 2 else 2
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jl%d' % os.getpid())
e.load(os.environ.get('ST', 'states/jr_t1_bomblist.st')); e.step(0, 0, 0, 2)
e.step(A, 0, 0, 2)
for i in range(25): e.step(0, 0, 0, 2)
assert bstate(e) == 17, bstate(e)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed (on the target screen)
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
s = seed; seen = []; log = []
JR = lambda: e.u32(BSTATUS + 0xE0)
for f in range(3000):
    b = bstate(e)
    press = f == 0 or (f > 10 and f < 200 and f % MASH == 0)
    e.step(A if press else 0, 0, 0, 2)
    for x in e.dbg_events():
        mx = x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)
        s, v = rand_int(s, mx)
        if x['ra'] in (0x800269AC, 0x80146D54): continue
        log.append((f, hex(x['ra']), mx, v))
    b = bstate(e)
    if not seen or seen[-1] != b: seen.append(b)
    if b == 13 and f > 100: break
a = JR()
cc = [v for f_, ra, mx, v in log if ra == '0x80277518']
print('RES seed %08x mash %d: CC rolls %s | Mario HP %d | Jr HP %d | end %d' % (seed, MASH, cc, e.s8(PLAYER_DATA + 2), e.s8(a + 0x1B8), f))
if os.environ.get('Q'): sys.exit(0)
c = collections.OrderedDict()
for f_, ra, mx, v in log: c.setdefault((f_, ra, mx), []).append(v)
for (f_, ra, mx), vs in c.items(): print(f_, ra, mx, len(vs), vs[:3])
