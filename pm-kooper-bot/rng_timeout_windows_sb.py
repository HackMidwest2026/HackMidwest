"""Time Out vs Hallway Bowser: success (roll <= 30) as a function of the frame of the target-confirm A, for a
fixed seed; also the seed steps from the confirm to the roll. Fast core: the roll is the first draw on the frame
the status is decided; it is found by replaying the seed model against Bowser's STOP status."""
import sys, os
from emu import *
from pm import *
from btl import *
from rngsim import *
seed = int(sys.argv[1], 16); D0, D1 = int(sys.argv[2]), int(sys.argv[3])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/tw%d' % os.getpid())
def bowser():
    for i in range(24):
        a = e.u32(BSTATUS + 0xE0 + 4 * i)
        if 0x80000000 < a < 0x80800000: return a
def run(d):
    e.load('states/boss_2302_on_timeout_sb.st'); e.step(0, 0, 0, 2)
    e.w32(SEED, seed); e.w32(SEED2, seed)                      # DIAGNOSTIC: chosen seed
    for i in range(14 + d): e.step(A if i == 2 else 0, 0, 0, 2)
    e.step(A, 0, 0, 2); e.step(A, 0, 0, 2)                    # target confirm (2 frames held, as above)
    sc = e.u32(SEED); seeds = []
    for i in range(400):
        seeds.append(e.u32(SEED)); e.step(0, 0, 0, 2)
        a = bowser()
        if a and e.s8(a + 0x210) == 8: return True, sc, i
    return False, sc, seeds
res = []; lat = set()
for d in range(D0, D1):
    ok, sc, k = run(d)
    res.append('S' if ok else '.')
    if ok: lat.add(k)
print('frames from confirm to STOP when it worked:', sorted(lat)); print('seed %08x confirm delays %d..%d: %s  (S = Time Out worked)' % (seed, D0, D1 - 1, ''.join(res)))
