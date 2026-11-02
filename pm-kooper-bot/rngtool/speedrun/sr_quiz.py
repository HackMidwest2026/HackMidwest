"""Quiz-room frames through the page's coin-present test. DIAGNOSTIC: GF_KPA82_PassedThroughDoor set to start the
door's event (as pressing A at the face door does); A pressed every 25 frames to advance text, choices at default."""
import subprocess, sys, os, numpy as np
from PIL import Image
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '/tmp/claude-0/pm/bot1')
from emu import *
from pm import *
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/srq')
for i in range(60): e.step(0, 0, 0, 2)
e.load('states/kpa82_e0.st'); e.step(0, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
n = 0x623; a = SAVE + 0x0FB0 + 4 * (n // 32); e.w32(a, e.u32(a) | (1 << (n % 32)))   # DIAGNOSTIC: start the door event
box = (0.78, 0.02, 0.065, 0.09); res = []
for f in range(int(sys.argv[2]) if len(sys.argv) > 2 else 3000):
    e.step(A if f % 25 == 0 else 0, 0, 0, 2)
    if f % 10: continue
    raw = subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '-resize', '320x240!', '-depth', '8', 'rgb:-'], capture_output=True, check=True).stdout
    im = Image.frombytes('RGB', (320, 240), raw)
    bar = np.asarray(im.crop((40, 3, 300, 6))).reshape(-1, 3).astype(int); vis = np.mean((bar[:, 0] > 150) & (bar[:, 1] > 120) & (bar[:, 2] < 120)) > 0.5
    x0, y0 = box[0] * 320, box[1] * 240
    a_ = np.asarray(im.crop((int(x0), int(y0), int(x0 + box[2] * 320 + .5), int(y0 + box[3] * 240 + .5))).resize((32, 32), Image.BILINEAR)).reshape(-1, 3).astype(int)
    r, g, b = a_[:, 0], a_[:, 1], a_[:, 2]; white = (r > 200) & (g > 200) & (b > 190); gold = ~white & (r > 140) & (g > 95) & (b < 120) & (r > b + 60)
    pres = gold.mean() + white.mean() > 0.3
    res.append((f, int(vis), int(pres), round(gold.mean(), 2), round(white.mean(), 2)))
    if pres and not vis and sum(1 for x in res if x[2] and not x[1]) % 20 == 1: im.save('%s/q_%05d.png' % (OUT, f))
print('sampled', len(res), 'bar visible', sum(x[1] for x in res), 'present', sum(x[2] for x in res), 'present w/o bar', sum(1 for x in res if x[2] and not x[1]))
print(''.join('P' if x[2] and not x[1] else ('#' if x[1] else '.') for x in res))
