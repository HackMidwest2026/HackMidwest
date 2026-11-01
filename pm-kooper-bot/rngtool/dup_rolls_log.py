"""Duplighosts x4, Bombette out: all rand_int calls from Bombette's do-nothing confirm (frame 0) through the enemy turn.
DIAGNOSTIC: seed set at the menu. usage: _duplog.py SEED [verbose]"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from emu import *
from btl import *
from rngsim import *
seed = int(sys.argv[1], 16); V = len(sys.argv) > 2
e = Emu('pm-jp.z64', '/dev/shm/pmbot/dl%d' % os.getpid())
e.load('states/dup_bomb_donothing.st'); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
s = seed; rolls = []; calls = collections.OrderedDict(); seen = []
for f in range(2500):
    e.step(A if f == 0 else 0, 0, 0, 2)
    for x in e.dbg_events():
        mx = x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)
        s, v = rand_int(s, mx)
        ra = x['ra']
        if ra in (0x800269AC,): continue
        if ra == 0x80146D54: calls.setdefault(f, []).append('coin'); continue
        calls.setdefault(f, []).append((hex(ra), mx))
        if ra == 0x802D46E0 and mx == 1000: rolls.append((f, v))
    b = bstate(e)
    if not seen or seen[-1] != b: seen.append(b)
    if b == 13 and f > 50: break
print('seed %08x: copy rolls (frame, value) %s; states %s; end frame %d' % (seed, rolls, seen, f))
if V:
    for f, c in calls.items():
        cc = collections.Counter(map(str, c)); print(f, dict(cc))
