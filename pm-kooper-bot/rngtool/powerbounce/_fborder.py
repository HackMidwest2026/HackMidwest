"""(run from bot1/) Find same-frame draw orderings in the FB2 Power Bounce. DIAGNOSTIC: seed + Bowser HP 127 written.
For each (seed, delay) given on stdin ('SEED D' lines), runs to the bounce end and prints frames with >1 draw class.
Also prints the roll values (ra 802a1168) so a model can be checked."""
import sys, os
from emu import *
from pm import *
from btl import *
from rngsim import *
CLS = {0x80146D54: 'C', 0xE00BC194: 'L', 0x802A1168: 'R', 0xE00861EC: 'T', 0x800269AC: 'S'}
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fbo%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT)
for line in sys.stdin:
    if not line.strip(): continue
    sd, d = line.split(); seed, d = int(sd, 16), int(d)
    e.dbg_log(0); e.load('states/fb2_t7like_pb.st'); e.step(0, 0, 0, 2)
    e.w32(SEED, seed); e.w32(SEED2, seed); e.w8(e.u32(BSTATUS + 0xE0) + 0x1B8, 127)   # DIAGNOSTIC
    e.dbg_log(1); e.dbg_events()
    PRESS = {d} | {d + 44 + 27 * k for k in range(16)}
    s = seed; rolls = []; mixed = []; other = set(); lastroll = -1
    for f in range(d + 71 + 27 * 14):
        e.step(A if f in PRESS else 0, 0, 0, 2)
        seq = ''
        for x in e.dbg_events():
            mx = x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)
            s, v = rand_int(s, mx)
            c = CLS.get(x['ra'], '?')
            if c == '?': other.add((f, hex(x['ra']), mx))
            if c == 'R': rolls.append((f, v)); lastroll = f
            if not seq or seq[-1] != c: seq += c
        if len(set(seq) - {'S'}) > 1: mixed.append('%d:%s' % (f, seq))
        if lastroll >= 0 and f > lastroll + 40: break
    print('RES %08x %d rolls %s mixed %s other %s' % (seed, d, ' '.join('%d=%d' % r for r in rolls), ' '.join(mixed), sorted(other)[:5]), flush=True)
