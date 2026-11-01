from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/tos')
e.load('states/boss_2302_to_menu_sb.st'); e.step(0, 0, 0, 2)
seq = [(0,0,0,10),(0,0,-70,2),(0,0,0,12),(0,0,-70,2),(0,0,0,12),(A,0,0,2),(0,0,0,20)] + [(0,0,70,2),(0,0,0,6)] * 3 + [(0,0,0,10)]
for b, x, y, n in seq:
    for i in range(n): e.step(b if i == 0 else 0, x, y, 2)
e.save('states/boss_2302_on_timeout_sb.st'); e.step(0, 0, 0, 2); print('saved')
