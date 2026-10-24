"""Reproduce one omo11_apg_grid.py run (DIR D W), check the menu fields, then press down, A and watch what happens:
curPartner, game mode, and whether the game keeps polling input (a crash/hang stops polls).
usage: omo11_apg_select.py DIR D W"""
import os, sys, signal
signal.signal(signal.SIGALRM, lambda *a: (print("HANG: game stopped polling input (no frames advance) at step", STEP[0], flush=True), os._exit(3)))
STEP = [0]
os.environ.setdefault('START', 'states/omo11_route_underblock.st')
import omo11_superblock_probe as P
from nav import go_to, stick_world, world_yaw_to
from emu import *
from pm import *
e = P.e
d, D, W = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
P.setup()
for i in range(D):
    p = P.player(e); e.step(0, *stick_world(e, world_yaw_to(p, -115 + d * 200, -112)), 2)
go_to(e, -115, -112, maxf=120, tol=1.5)
for i in range(W): e.step(0, 0, 0, 2)
for i in range(6): e.step(A, 0, 0, 2)
p = None
for f in range(900):
    p = P.popup()
    if p: break
    e.step(A if f % 8 == 0 else 0, 0, 0, 2)
print('menu', P.dump(p))
for i in range(40): e.step(0, 0, 0, 2)
for i in range(2): e.step(0, 0, -80, 1)
for i in range(10): e.step(0, 0, 0, 2)
for i in range(2): e.step(A, 0, 0, 1)
for f in range(1200):
    pl = e.polls; STEP[0] = f; signal.alarm(20)
    try:
        e.step(A if (f > 150 and f % 30 == 0) else 0, 0, 0, 2)
    except RuntimeError as x:
        print('emulator stopped at', f, x); break
    if f % 20 == 0:
        print(f, 'result', e.s32(p + 0x32C), 'curPartner', e.s8(PLAYER_DATA + 0x12), 'mode', e.s16(GAME_MODE),
              'polling', e.polls != pl, 'Mario', round(P.player(e)['x']), round(P.player(e)['y']))
