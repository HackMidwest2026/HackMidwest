"""(run from bot1/) FB2: DIAGNOSTIC Life Shroom in slot 0 + Mario HP 1, then mash a turn so Bowser attacks; log battle
states, HP, screenshots on state changes. usage: DISPLAY=... M64P_GFX=... _fbdie.py OUT [N]"""
import sys, os, subprocess
from emu import *
from pm import *
from btl import *
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True); N = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fbd%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.load('states/fb2_t7like_menu.st'); e.step(0, 0, 0, 2)
e.w16(PLAYER_DATA + 0x1B4, 0x95); e.w8(PLAYER_DATA + 2, 1)      # DIAGNOSTIC: a Life Shroom, Mario 1 HP
last = None
for f in range(N):
    b = bstate(e); hp = e.s8(PLAYER_DATA + 2)
    key = (b, hp)
    if key != last:
        print(f, 'bstate', b, 'hp', hp, flush=True)
        subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '%s/f%05d_b%d.png' % (OUT, f, b)], check=True)
        last = key
    if f % 150 == 0: subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '%s/p%05d.png' % (OUT, f)], check=True)
    e.step(A if f % 20 == 0 else 0, 0, 0, 2)
