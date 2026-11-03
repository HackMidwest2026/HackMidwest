"""Step a scripted input list from a state, screenshot after each entry (glide64), print battle state / HP / FP.
Run from /tmp/claude-0/pm/bot1:
  DISPLAY=:91 M64P_GFX=/usr/lib/x86_64-linux-gnu/mupen64plus/mupen64plus-video-glide64mk2.so M64P_DATA=/usr/share/games/mupen64plus \
  PYTHONPATH=. python3 nav.py STATE OUTDIR '[[btn,x,y,n],...]' [--menu] [--hp N] [--save PATH]
--menu: first advance to Mario's first menu (A every 15 frames outside menus).
--hp N: DIAGNOSTIC write of Mario's HP (gPlayerData.curHP) after the load (setup only)."""
import sys, os, json, subprocess
sys.path.insert(0, os.getcwd())
from emu import *
from pm import *
from btl import *
st, OUT, seq = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/nav%d' % os.getpid())
for i in range(60): e.step(0, 0, 0, 2)
e.load(st); e.step(0, 0, 0, 2)
if '--hp' in sys.argv: e.w8(PLAYER_DATA + 2, int(sys.argv[sys.argv.index('--hp') + 1]))   # DIAGNOSTIC: Mario HP
if '--menu' in sys.argv: to_first_menu(e)
def shot(name):
    if os.environ.get('M64P_GFX'):
        subprocess.run(['import', '-window', 'root', '-crop', '640x480+80+60', '+repage', '%s/%s.png' % (OUT, name)], check=True)
shot('s_start'); f = 0
for i, (b, x, y, n) in enumerate(seq):
    for k in range(n): e.step(b if k == 0 else 0, x if k == 0 else 0, y if k == 0 else 0, 2); f += 1
    shot('s%02d' % i)
    print(i, f, 'bstate', bstate(e), 'hp', e.s8(PLAYER_DATA + 2), 'fp', e.s8(PLAYER_DATA + 5), flush=True)
if '--save' in sys.argv: e.save(sys.argv[sys.argv.index('--save') + 1])
