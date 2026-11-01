# (run from the emulator working dir, bot1/) """Find the guard timing for Bowser's T1 attack: replay _hw1log2's inputs (same seed and random delays, plain core),
note the frame Mario's HP drops, then retry pressing A k frames before it; report damage per k."""
import sys, os, random
from emu import *
from pm import *
from btl import *
from rngsim import *
seed, dseed = int(sys.argv[1], 16), int(sys.argv[2])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/hg%d' % os.getpid())
def play(guard_at=None):
    rnd = random.Random(dseed); F = [0]; hp = []
    e.load('states/boss_2302_route_menu.st'); e.step(0, 0, 0, 2); e.w32(SEED, seed); e.w32(SEED2, seed)   # DIAGNOSTIC: chosen seed
    def step(b=0, x=0, y=0):
        if guard_at is not None and F[0] == guard_at: b = A
        e.step(b, x, y, 2); F[0] += 1; hp.append(e.s8(PLAYER_DATA + 2))
    def w(n, b=0, x=0, y=0):
        for i in range(n): step(b if i == 0 else 0, x, y if i == 0 else 0)
    def until(states, cap=4000):
        for f in range(cap):
            if bstate(e) in states: return
            step()
    def confirm(): w(rnd.randint(0, 40)); step(A)
    w(15, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); confirm(); until([14]); w(10)
    w(25, A); w(25, A); until([17], cap=80); confirm()
    for f in range(40 + rnd.randint(0, 8)): step()
    for f in range(10 + rnd.randint(0, 4)): step(0, 70, 0)
    until([13]); return hp
hp = play(); drop = next(i for i in range(1, len(hp)) if hp[i] < hp[i - 1]); print('no guard: HP', hp[-1], 'hit at frame', drop)
res = []
for k in range(0, 14):
    h = play(drop - k); res.append((k, h[-1]))
print('A k frames before the hit -> Mario HP after:', res)
