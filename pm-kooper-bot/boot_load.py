"""Power on with DATADIR's save file, go through the title and file select with A presses, and stop once the
saved file is loaded (field mode, omo_10). usage: boot_load.py DATADIR OUT.st"""
import os, sys
from emu import *
from pm import *
e = Emu('pm-jp.z64', sys.argv[1])
for f in range(6000):
    m = e.s16(GAME_MODE)
    if f % 50 == 0: print(f, 'mode', m, where(e) if m == 4 else '', flush=True)
    if m == 4 and where(e)[:2] == (16, 9):
        break
    e.step(A if f % 20 == 0 else 0, 0, 0, 2)
for i in range(60): e.step(0, 0, 0, 2)
print('loaded', where(e), player(e), 'partner', e.s8(PLAYER_DATA + 0x12), 'frame', e.frame, flush=True)
e.save(sys.argv[2]); e.step(0, 0, 0, 2)
