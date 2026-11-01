"""Footage for the press-timing readout: turn-1 menu (seed), Time Out target screen, confirm on a known frame."""
import os, subprocess, json
from emu import *
from pm import *
from btl import *
from rngsim import *
OUT = '/dev/shm/pmbot/vid'; os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))
SH = 700 * (0xFFFFFFFF // 1010)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rv2')
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/boss_2302_run_menu.st'); e.step(0, 0, 0, 2)
seed = 0x5eed1234; e.w32(SEED, seed); e.w32(SEED2, seed)          # DIAGNOSTIC: known seed for the test
truth = []; F = [0]; marks = {}
def step(b=0, x=0, y=0):
    prev = e.u32(SEED); e.step(b, x, y, 2); cur = e.u32(SEED)
    k = 0; t = prev
    while t != cur and k < 5000: t = adv(t); k += 1
    if k == 2 and bstate(e) in (13, 17): truth.append({'frame': F[0], 'seed_before': prev, 'shine': adv(prev) >= SH})
    subprocess.run(['import', '-window', 'root', '-crop', '592x400+104+100', '+repage', '-resize', '296x200!', '%s/f%05d.png' % (OUT, F[0])], check=True)
    F[0] += 1
def wait(n):
    for i in range(n): step()
wait(1500)
MENU = {5: (0, 0, -70), 13: (0, 0, -70), 21: (A, 0, 0), 31: (0, 0, 70), 37: (0, 0, 70), 43: (0, 0, 70), 51: (A, 0, 0)}
for i in range(60): step(*MENU.get(i, (0, 0, 0)))
marks['target_screen'] = F[0]; wait(150)
marks['confirm'] = F[0]; step(A); step(A); wait(200)
json.dump({'truth': truth, 'marks': marks, 'frames': F[0]}, open('/dev/shm/pmbot/vid3_truth.json', 'w'))
print('frames', F[0], 'marks', marks, 'coin draws in menus', len(truth))
