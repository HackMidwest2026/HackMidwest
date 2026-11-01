import subprocess
from emu import *
from pm import *
from PIL import Image
out = '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/trans'
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cu4')
for i in range(150): e.step(0, 0, 0, 2)
e.load('states/kkj12_e0.st'); e.step(0, 0, 0, 2)
for i in range(30): e.step(0, 0, 0, 2)
vis = []
for t in range(0, 300):
    x = 80 if (t // 60) % 2 == 0 else -80
    e.step(U_CBUTTON if t == 0 else 0, x, 0, 2)
    if t % 5 == 0:
        p = '%s/v.png' % out; subprocess.run(['import', '-window', 'root', p], check=True)
        im = Image.open(p).convert('RGB').crop((140, 102, 660, 108)); px = list(im.getdata())
        gold = sum(1 for r, g, b in px if r > 150 and g > 120 and b < 120) / len(px)
        vis.append((t, gold > 0.5))
on = [t for t, v in vis if v]
print('bar visible from frame %s to %s after one C-up press (sampled every 5)' % (on[0] if on else None, on[-1] if on else None))
print(''.join('#' if v else '.' for t, v in vis))
