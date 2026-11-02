"""(run from bot1/) Trace every rand_int call in the FB2 Power Bounce from states/fb2_t7like_pb.st.
DIAGNOSTIC: seed written at frame 0, Bowser HP 127. Presses: A at D, then A at D+44+27k (LEAD env shifts them).
usage: _fbtrace.py SEED D [N]   prints per-frame draws (frame, ra, max, value) except the per-frame step."""
import sys, os, collections
from emu import *
from pm import *
from btl import *
from rngsim import *
seed, d = int(sys.argv[1], 16), int(sys.argv[2]); N = int(sys.argv[3]) if len(sys.argv) > 3 else 500
lead = int(os.environ.get('LEAD', '0'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fbt%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.load('states/fb2_t7like_pb.st'); e.step(0, 0, 0, 2)
e.w32(SEED, seed); e.w32(SEED2, seed); e.w8(e.u32(BSTATUS + 0xE0) + 0x1B8, 127)     # DIAGNOSTIC: seed, Bowser HP 127
e.bp_add(RAND_INT); e.dbg_log(1); e.dbg_events()
PRESS = {d} | {d + 44 + 27 * k - lead for k in range(16)}
hp = lambda: e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8)
s = seed; last = hp(); hits = 0
for f in range(N):
    e.step(A if f in PRESS else 0, 0, 0, 2)
    per = collections.Counter(); out = []
    for x in e.dbg_events():
        mx = x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)
        s, v = rand_int(s, mx)
        if x["ra"] == 0x800269AC: per["step"] += 1; out.append("S"); continue
        out.append('%x:%d=%d' % (x['ra'], mx, v))
    h = hp()
    if h < last: hits += 1; out.append('HIT%d hp%d' % (hits, h))
    last = h
    if out: print(f, per['step'], ' '.join(out))
print('BOUNCES', hits)
