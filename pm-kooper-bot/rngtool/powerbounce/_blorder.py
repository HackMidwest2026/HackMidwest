"""(run from bot1/) Blooper Power Bounce from states/blooper_pb.st: log every rand_int per frame and check the model.
DIAGNOSTIC: seed written at frame 0, action commands on, Blooper HP set to 127 so every bounce fits.
stdin lines 'SEED D'. Presses: A at D, then A at D+49+26k (2 frames before each HP drop at D+51+26k).
Prints roll values (ra 802a1168), same-frame orders, and unknown draw sources."""
import sys, os
from emu import *
from pm import *
from btl import *
from rngsim import *
CLS = {0x80146D54: 'C', 0x802A1168: 'R', 0xE00861EC: 'T', 0x800269AC: 'S'}
e = Emu('pm-jp.z64', '/dev/shm/pmbot/blo%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.bp_add(RAND_INT)
HP127 = os.environ.get('HP127', '1') == '1'
for line in sys.stdin:
    if not line.strip(): continue
    sd, d = line.split(); seed, d = int(sd, 16), int(d)
    e.dbg_log(0); e.load('states/blooper_pb.st'); e.step(0, 0, 0, 2)
    e.w32(SEED, seed); e.w32(SEED2, seed)                                   # DIAGNOSTIC: seed
    e.w8(PLAYER_DATA + 0xA, 1)                                              # DIAGNOSTIC: action commands on
    if os.environ.get('DM') == '1': e.w16(PLAYER_DATA + 0x20A, 0xE3)       # DIAGNOSTIC: Dodge Master equipped (2nd badge slot)
    if HP127: e.w8(e.u32(BSTATUS + 0xE0) + 0x1B8, 127)                       # DIAGNOSTIC: Blooper HP 127
    e.dbg_log(1); e.dbg_events()
    PRESS = {d} | {d + int(os.environ.get("PB", "49")) + 26 * k for k in range(40)}
    s = seed; rolls = []; mixed = []; other = {}; lastroll = -1; first = {}
    for f in range(d + 76 + 26 * 40):
        e.step(A if f in PRESS else 0, 0, 0, 2)
        seq = ''
        for x in e.dbg_events():
            mx = x['a0'] if x['a0'] < 0x80000000 else x['a0'] - (1 << 32)
            s, v = rand_int(s, mx)
            c = CLS.get(x['ra'], '?')
            if c == '?': other.setdefault(hex(x['ra']), []).append(f)
            if c == 'R': rolls.append((f, v)); lastroll = f
            first.setdefault(c, f)
            if not seq or seq[-1] != c: seq += c
        if len(set(seq) - {'S'}) > 1: mixed.append('%d:%s' % (f, seq))
        if lastroll >= 0 and f > lastroll + 40: break
    oth = ' '.join('%s@%s' % (k, ','.join(map(str, v[:6]))) for k, v in other.items())
    print('RES %08x %d rolls %s mixed %s other %s' % (seed, d, ' '.join('%d=%d' % r for r in rolls), ' '.join(mixed[:20]), oth), flush=True)
