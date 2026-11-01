import os, subprocess, json
from emu import *
from pm import *
from rngsim import *
OUT = '/dev/shm/pmbot/vid'; os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))
SH = 700 * (0xFFFFFFFF // 1010)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/rv')
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/boss_2302_run_menu.st'); e.step(0, 0, 0, 2)
seed = 0x5eed1234; e.w32(SEED, seed); e.w32(SEED2, seed)          # DIAGNOSTIC: known seed for the test
truth = []
N = int(os.environ.get('N', 2100))
for f in range(N):
    prev = e.u32(SEED); e.step(0, 0, 0, 2); cur = e.u32(SEED)
    k = 0; t = prev
    while t != cur and k < 50: t = adv(t); k += 1
    if k == 2: truth.append({'frame': f, 'seed_before': prev, 'shine': adv(prev) >= SH})
    subprocess.run(['import', '-window', 'root', '-crop', '592x400+104+100', '+repage', '-resize', '296x200!', '%s/f%05d.png' % (OUT, f)], check=True)
json.dump(truth, open('/dev/shm/pmbot/vid_truth.json', 'w'))
print('frames', N, 'coin draws', len(truth), 'shines', sum(t['shine'] for t in truth))
