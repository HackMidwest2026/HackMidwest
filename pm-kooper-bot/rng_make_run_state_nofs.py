"""states/boss_2302_run_menu.st: Hallway Bowser at Mario's first menu, set up like the real run (DIAGNOSTIC setup):
Super Jump Charge (0x10C) equipped, 7 star spirits + Star Beam, full SP, 50 FP, 99 HP."""
from emu import *
from pm import *
from btl import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mkr')
e.load('states/boss_2302_nofs_start.st'); e.step(0, 0, 0, 2)
s = [e.u16(PLAYER_DATA + 0x208 + 2 * i) for i in range(64)]
if 0x10C not in s: e.w16(PLAYER_DATA + 0x208 + 2 * s.index(0), 0x10C)      # DIAGNOSTIC setup: Super Jump Charge
e.w8(PLAYER_DATA + 0x28E, 7); e.w16(PLAYER_DATA + 0x290, 7 * 256); e.w8(PLAYER_DATA + 0x292, 1)   # DIAGNOSTIC: spirits, SP, Star Beam
for o in (2, 3, 4): e.w8(PLAYER_DATA + o, 99)
for o in (5, 6, 7): e.w8(PLAYER_DATA + o, 50)                                # DIAGNOSTIC setup: FP
n = to_first_menu(e); print('menu after', n)
e.save('states/boss_2302_run_menu.st'); e.step(0, 0, 0, 2)
