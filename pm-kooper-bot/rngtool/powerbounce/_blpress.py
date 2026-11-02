"""(run from bot1/) (run from bot1/) Blooper Power Bounce from states/blooper_pb.st: confirm at frame D, then find each landing iteratively
(press 1 frame before the observed hit). Prints hit frames. usage: _blpress.py SEEDHEX D"""
import os, sys
from emu import *
from pm import *
from btl import *
from rngsim import *
seed, D = int(sys.argv[1], 16), int(sys.argv[2])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/bp%d' % os.getpid())
def run(press, N=900):
    e.load('states/blooper_pb.st'); e.step(0, 0, 0, 2)
    e.w32(SEED, seed); e.w32(SEED2, seed)                    # DIAGNOSTIC: seed
    e.w8(PLAYER_DATA + 0xA, 1)                                # DIAGNOSTIC: action commands on (save is from before the Lucky Star)
    hp = lambda: e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8); last = hp(); hits = []
    for f in range(N):
        e.step(A if f in press else 0, 0, 0, 2); h = hp()
        if h < last: hits.append(f)
        last = h
        if f > 60 and bstate(e) not in (17, 18, 19): break
    return hits, hp()
press = {D}; hits, h = run(press)
while len(press) < 40:
    press = {D} | {x - int(os.environ.get("PO", "3")) for x in hits}
    h2, hp2 = run(press)
    if len(h2) <= len(hits): break
    hits, h = h2, hp2
print('PRESS', sorted(press)); print('HITS', hits, 'n', len(hits), 'gaps', [b - a for a, b in zip(hits, hits[1:])], 'Blooper HP', h)
