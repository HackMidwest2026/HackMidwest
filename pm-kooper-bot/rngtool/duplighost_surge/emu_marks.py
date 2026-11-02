"""Emulator side of the clip timing check (glide64 screenshots): frames from the Change Member confirm (the A step)
to the first Duplighost's transform ring (yellow/pink), and from the last throw to Mario's menu (gBattleState 13).
usage (from /tmp/claude-0/pm/bot1): DISPLAY=... M64P_GFX=.../mupen64plus-video-glide64mk2.so M64P_DATA=... M64P_DBG=1
  PYTHONPATH=. python3 .../emu_marks.py SEED SHOTDIR"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.getcwd())
import numpy as np
from PIL import Image
from dsurge import *
seed = int(sys.argv[1], 16); SD = sys.argv[2]
r = Run(seed, shots={'dir': SD, 'on': False}, tag='e')
r.surge(1, 1); r.to_mario_menu()
L = r.spinies()[-1]
r.switch([20, 30, 35, 45, 60, 70])
C = r.marks['confirm']
r.shots['on'] = True
for i in range(140): r.step()
r.shots['on'] = False
r.enemy_turn()
print('last throw %d, Mario menu %d (+%d), confirm %d, rolls %s, partner %d' % (L, r.marks['mario_menu'], r.marks['mario_menu'] - L, C, r.copy_rolls(), r.partner()))
for f in range(C + 56, C + 141):                 # the ring cannot come before the first roll (C+56); earlier purple = the partner swap
    p = os.path.join(SD, 'e%05d.png' % f)
    im = np.asarray(Image.open(p).convert('RGB')).astype(int); R_, G, B_ = im[..., 0], im[..., 1], im[..., 2]
    # glide64 draws the ring purple (the console capture shows it yellow -> pink)
    ring = int(((R_ > 90) & (B_ > 90) & (G < 70) & (abs(R_ - B_) < 80))[60:420].sum())
    if ring > 3000: print('first ring frame: shot after step %d = confirm + %d (%d px)' % (f, f - C, ring)); break
