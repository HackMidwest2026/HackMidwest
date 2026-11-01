"""states/boss_2302_to_menu.st: Hallway Bowser at Mario's first menu with 7 star spirits and full SP, 99 HP
(DIAGNOSTIC setup), so Time Out is in the Star Spirit menu."""
from emu import *
from pm import *
from btl import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mkto')
e.load('states/boss_2302_start.st'); e.step(0, 0, 0, 2)
e.w8(PLAYER_DATA + 0x28E, 7); e.w16(PLAYER_DATA + 0x290, 7 * 256)      # DIAGNOSTIC setup: 7 star spirits, full SP
for o in (2, 3, 4): e.w8(PLAYER_DATA + o, 99)                          # DIAGNOSTIC setup: Mario survives
n = to_first_menu(e); print('menu after', n)
e.save('states/boss_2302_to_menu.st'); e.step(0, 0, 0, 2)
