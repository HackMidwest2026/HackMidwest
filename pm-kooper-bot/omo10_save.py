"""omo_10: walk under the save block (150, 60, 55), jump into it and save with A (inputs only).
The save goes to DATADIR's flash file. usage: omo10_save.py DATADIR"""
import os, sys
from emu import *
from pm import *
from nav import go_to
e = Emu('pm-jp.z64', sys.argv[1])
e.load('states/omo10_e0_goompa.st'); e.step(0, 0, 0, 2)
print('start', player(e), flush=True)
go_to(e, 150, 55, maxf=600, tol=2); print('under block', player(e), flush=True)
for i in range(10): e.step(0, 0, 0, 2)
for i in range(6): e.step(A, 0, 0, 2)
for f in range(1500):
    e.step(A if f % 10 == 0 else 0, 0, 0, 2)
for i in range(200): e.step(0, 0, 0, 2)
print('end', where(e), player(e), 'mode', e.s16(GAME_MODE), flush=True)
