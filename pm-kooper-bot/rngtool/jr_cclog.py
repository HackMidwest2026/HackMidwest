"""From a decisive-point state (ST), press A on frame 0 and log the rand_int calls until Mario's next menu.
Prints the Close Call rolls (ra 0x80277518) and, with V=1, every other non-frame non-coin draw. usage: _cclog.py SEED"""
import sys, os, collections
from emu import *
from pm import *
from btl import *
from rngsim import *
seed = int(sys.argv[1], 16)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cc%d' % os.getpid())
e.load(os.environ['ST']); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
s = seed; log = []; seen = []
for f in range(3000):
    G = os.environ.get('GUARD', '')
    gset = set(int(x) for x in G.split(',') if x) if G != 'mash' else set(range(100, 260, 2))
    e.step(A if (f == 0 or f in gset) else 0, 0, 0, 2)
    for x in e.dbg_events():
        mx = x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)
        s, v = rand_int(s, mx)
        if x['ra'] in (0x800269AC, 0x80146D54): continue
        log.append((f, hex(x['ra']), mx, v))
    b = bstate(e)
    if not seen or seen[-1] != b: seen.append(b)
    if b == 13 and f > 100: break
cc = [(f_, v) for f_, ra, mx, v in log if ra == '0x80277518']
print('RES seed %08x: CC %s | Mario HP %d | end %d' % (seed, cc, e.s8(PLAYER_DATA + 2), f))
if os.environ.get('V'):
    c = collections.OrderedDict()
    for f_, ra, mx, v in log:
        if cc and f_ > cc[0][0]: break
        c.setdefault((f_, ra, mx), []).append(v)
    for k, vs in c.items(): print('  ', k, len(vs))
