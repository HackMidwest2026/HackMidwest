"""When is the status bar on screen around the hallway scene (B held)? From states/kkj13_e0.st: C-up pressed on frame 2
(DIAGNOSTIC: the state starts at the room entry; the runner would have it up from the walk), then B held to Mario's T1
menu. Per frame: bar visible (gold pixels in the bar row, as speedrun/sr_run.py), game mode, battle state, RNG steps.
usage: DISPLAY=:9x M64P_GFX=<glide64mk2 .so> M64P_DATA=<dir with Glide64mk2.ini> python3 zw_barvis.py"""
import os, sys, subprocess
import numpy as np
from PIL import Image
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
from emu import *; from pm import *; from rngsim import *; from btl import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/zwbar')
for i in range(60): e.step(0, 0, 0, 2)
e.load('states/kkj13_e0.st'); e.step(0, 0, 0, 2)
def vis():
    raw = subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '-resize', '640x480!', '-depth', '8', 'rgb:-'], capture_output=True, check=True).stdout
    im = Image.frombytes('RGB', (640, 480), raw); bar = np.asarray(im.crop((80, 6, 600, 12))).reshape(-1, 3).astype(int)
    return float(np.mean((bar[:, 0] > 150) & (bar[:, 1] > 120) & (bar[:, 2] < 120)))
prev_v = None; changes = []
for f in range(700):
    b = B | (U_CBUTTON if f == 2 else 0)
    e.step(b, 0, 0, 2); v = vis() > 0.5; m = e.s16(GAME_MODE); bs = bstate(e) if m == 8 else -1
    if v != prev_v: changes.append((f, 'bar ' + ('up' if v else 'hidden'), m, bs)); prev_v = v
    if m == 8 and bs == 13: changes.append((f, 'T1 menu', m, bs)); break
print(changes)
