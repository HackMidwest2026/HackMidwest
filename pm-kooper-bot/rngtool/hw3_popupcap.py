# (run from bot1/) capture the screen around the Spiny Flip's aim popup (DIAGNOSTIC: HP 3, seed written). Replays hw3_log.py's
# inputs for SEED DSEED (same random delays), screenshots of the X display around the confirm and the throw into OUT/ (scratch only: never commit frames)
import sys, os, random, subprocess
from emu import *
from pm import *
from btl import *
from rngsim import *
seed, dseed, TK, OUT = int(sys.argv[1], 16), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]; rnd = random.Random(dseed)
rnd.randint(55, 115); rnd.randint(0, 1)          # as _hw3log.py without THROW_K / GUARD args
os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/hw3c%d' % os.getpid())
e.load('states/boss_2302_route_menu.st'); e.step(0, 0, 0, 2)
e.w8(PLAYER_DATA + 2, 3); e.w32(SEED, seed); e.w32(SEED2, seed)        # DIAGNOSTIC
n = [0]; shots = [None]
def step(b=0, x=0, y=0):
    e.step(b, x, y, 2); n[0] += 1
    if shots[0] is not None and shots[0][0] <= n[0] <= shots[0][1]:
        subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % n[0])], check=True)
def w(k, b=0, x=0, y=0):
    for i in range(k): step(b if i == 0 else 0, x, y if i == 0 else 0)
def until(states, cap=4000):
    for f in range(cap):
        if bstate(e) in states: return
        step()
def confirm(): w(rnd.randint(0, 40)); step(A)
w(15, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); confirm(); until([14]); w(10)
w(25, A); w(25, A); until([17], cap=80)
d = rnd.randint(0, 40); w(d); c = n[0]; shots[0] = (c - 1, c + 8); step(A)
s0 = rnd.randint(20, 40)
for f in range(s0): step()
for f in range(12 + rnd.randint(0, 4)): step(0, 70, 0)
shots[0] = (c + TK - 2, c + TK + 40)
while n[0] < c + TK: step()
step(A)
for f in range(42): step()
print('confirm at step', c + 1, '(A on step index', c, ') throw A on step index', c + TK)
