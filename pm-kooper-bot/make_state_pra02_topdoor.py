"""Make states/pra02_topdoor_closed.st, the start state for rmc_timing.py: from pra_04 just north of pra_02
(states/pra_north_of_pra02.st), equip Speedy Spin and Ultra Boots (DIAGNOSTIC setup writes: the run would have
them by now), hold DOWN, press A at the door, and stop on the first frame the pra_02 top door is fully closed
(57 frames after the A press; Mario stands at (500, -172), Lakilester out)."""
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mk')
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/pra_north_of_pra02.st'); e.step(0, 0, 0, 2)
for i in range(20): e.step(0, 0, -80, 2)
s = [e.u16(PLAYER_DATA + 0x208 + 2 * i) for i in range(64)]
if 0x11F not in s: e.w16(PLAYER_DATA + 0x208 + 2 * s.index(0), 0x11F)   # DIAGNOSTIC setup: Speedy Spin equipped
e.w8(PLAYER_DATA, 2)                                                        # DIAGNOSTIC setup: Ultra Boots
e.step(A, 0, -80, 2)
for f in range(57): e.step(0, 0, 0, 2)
e.save('states/pra02_topdoor_closed.st'); p = player(e); print('saved', where(e), p)
