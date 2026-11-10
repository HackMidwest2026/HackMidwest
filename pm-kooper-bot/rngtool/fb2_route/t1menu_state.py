"""v87 (state recreation): /dev/shm/fb2r/t1menu.st, the Final Bowser phase-2 T1 menu that route_build.py starts from:
states/boss_2304_peach_start.st (make_states.sh), A every 15 frames outside menus until Mario's first menu (as
fb_aura/aura_carry.py), then 20 idle frames. No RAM writes here (route_build writes HP / seed).
Run from /tmp/claude-0/pm/bot1:  PYTHONPATH=. python3 t1menu_state.py [OUT]"""
import sys, os
sys.path.insert(0, os.getcwd())
from emu import *
from pm import *
from btl import bstate
OUT = sys.argv[1] if len(sys.argv) > 1 else '/dev/shm/fb2r/t1menu.st'
os.makedirs(os.path.dirname(OUT), exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/t1m%d' % os.getpid())
e.load('states/boss_2304_peach_start.st'); e.step(0, 0, 0, 2)
n = 0
while bstate(e) != 13 and n < 3000:
    e.step(A if (n % 15 == 0 and bstate(e) not in (13, 14, 17)) else 0, 0, 0, 2); n += 1
e.step(0, 0, 0, 40)
print('T1 menu after', n, 'state', bstate(e), 'hp', e.s8(PLAYER_DATA + 2), 'fp', e.s8(PLAYER_DATA + 5))
e.save(OUT)
