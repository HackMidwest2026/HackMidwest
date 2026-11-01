"""Power Bounce vs Jr. Troopa from states/jr_t6_pb_target.st: confirm on frame 0, AC presses on the earliest window
frames (46, 73, 101, 129, 157, 185, 213, ...), log every non-frame non-coin rand_int call. usage: _pbjrlog.py SEED"""
import sys, os, collections
from emu import *
from pm import *
from btl import *
from rngsim import *
seed = int(sys.argv[1], 16)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/pj%d' % os.getpid())
e.load('states/jr_t6_pb_target.st'); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
PRESS = {0, 46, 73, 101, 129, 157, 185, 213, 241, 269, 297}
s = seed; log = []
for f in range(700):
    e.step(A if f in PRESS else 0, 0, 0, 2)
    for x in e.dbg_events():
        mx = x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)
        s, v = rand_int(s, mx)
        if x['ra'] in (0x800269AC, 0x80146D54): continue
        log.append((f, hex(x['ra']), mx, v))
    if bstate(e) not in (17, 18, 19) and f > 30: break
rolls = [(f_, v) for f_, ra, mx, v in log if ra == '0x802a1168']
print('RES seed %08x: cap rolls %s | Jr HP %d | end %d' % (seed, rolls, e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8), f))
if os.environ.get('V'):
    c = collections.OrderedDict()
    for f_, ra, mx, v in log: c.setdefault((f_, ra, mx), []).append(v)
    for k, vs in c.items(): print('  ', k, len(vs))
