"""Walk Mario from isk11_laki_ready.st to the lock ledge (y -470) with Laki following naturally; save the state."""
import math, sys
from emu import *
from pm import *
from corner_sweep import stick_for
PATH = [(-150, 580), (0, 610), (120, 590), (200, 530), (250, 480), (285, 445), (320, 420), (365, 405)]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/iwl')
e.load('states/isk11_laki_ready.st'); k = 0
lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
for i in range(900):
    q = player(e)
    if k < len(PATH) and math.hypot(PATH[k][0] - q['x'], PATH[k][1] - q['z']) < 8: k += 1
    if k == len(PATH): break
    st = stick_for(math.degrees(math.atan2(PATH[k][1] - q['z'], PATH[k][0] - q['x'])) % 360, 80)
    jump = k >= 5 and i % 30 < 12
    e.step(A if jump else 0, st[0], st[1], 2)
    if i % 20 == 0: L = lk(); print(i, k, round(q['x']), round(q['y']), round(q['z']), q['action'], 'laki', round(L['x']), round(L['y']), round(L['z']))
for i in range(60): e.step(0, 0, 0, 2)
q = player(e); L = lk(); print('end', q, L)
e.save('states/isk11_ledge.st')
