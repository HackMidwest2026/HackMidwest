"""(run from bot1/) step a scripted input list from a state and screenshot after each; DIAGNOSTIC writes as _fbdie.
usage: _fbnav.py OUT 'json [[btn,x,y,n,shot?],...]' """
import sys, os, subprocess, json
from emu import *
from pm import *
from btl import *
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fbn%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.load(os.environ.get('ST', 'states/fb2_t7like_menu.st')); e.step(0, 0, 0, 2)
if not os.environ.get('NODIAG'):
    e.w16(PLAYER_DATA + 0x1B4, 0x95); e.w8(PLAYER_DATA + 2, 1)      # DIAGNOSTIC: a Life Shroom, Mario 1 HP
f = 0
for i, (b, x, y, n) in enumerate(json.loads(sys.argv[2])):
    for k in range(n): e.step(b if k == 0 else 0, x if k == 0 else 0, y if k == 0 else 0, 2); f += 1
    subprocess.run(['import', '-window', 'root', '-crop', '592x390+104+96', '+repage', '%s/s%02d.png' % (OUT, i)], check=True)
    print(i, f, 'bstate', bstate(e), 'hp', e.s8(PLAYER_DATA + 2), flush=True)
if os.environ.get('SAVE'): e.save(os.environ['SAVE'])
