import os, subprocess, json
from emu import *
from pm import *
from btl import *
from rngsim import *
OUT = '/dev/shm/pmbot/vidx'; os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))
SH = 700 * (0xFFFFFFFF // 1010)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rv2')
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/boss_2302_run_menu.st'); e.step(0, 0, 0, 2)
seed = 0x5eed1234; e.w32(SEED, seed); e.w32(SEED2, seed)          # DIAGNOSTIC: known seed for the test
truth = []; F = [0]; marks = {}; allseed = []
def step(b=0, x=0, y=0):
    prev = e.u32(SEED); e.step(b, x, y, 2); cur = e.u32(SEED)
    k = 0; t = prev
    while t != cur and k < 5000: t = adv(t); k += 1
    allseed.append(prev)
    if k == 2 and bstate(e) in (13, 17): truth.append({'frame': F[0], 'seed_before': prev, 'shine': adv(prev) >= SH})
    pass
    F[0] += 1
def wait(n):
    for i in range(n): step()
wait(1500); marks['turn1'] = F[0]
step(A); wait(20); step(0, 0, -70); wait(12); step(A); wait(20); step(A)
for i in range(4000):
    b = bstate(e)
    if b == 14:
        wait(20); step(A); wait(20); step(A); wait(20); step(A); wait(10)
        for j in range(120): step(A if j % 4 == 0 else 0)
    elif b == 17: wait(8); step(A)
    elif b == 13 and i > 100: break
    else: step(B)
marks['turn2_menu'] = F[0]; wait(300)
MENU = {5: (0, 0, -70), 13: (0, 0, -70), 21: (A, 0, 0), 31: (0, 0, 70), 37: (0, 0, 70), 43: (0, 0, 70), 51: (A, 0, 0)}
for i in range(60): step(*MENU.get(i, (0, 0, 0)))
marks['target_screen'] = F[0]; wait(1200)
json.dump({'allseed': allseed, 'frames': F[0]}, open('/dev/shm/pmbot/vid2_allseed.json', 'w'))
print('frames', F[0], 'marks', marks, 'coin draws in menus', len(truth))
