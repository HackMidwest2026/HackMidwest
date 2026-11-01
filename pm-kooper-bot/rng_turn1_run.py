"""Play turn 1 like the run: Mario Super Jump Charge, Laki Spiny Flip (A presses through its action command), then
Bowser's turn (hold B for any text); stop at Mario's turn-2 menu. Saves states/boss_2302_turn2.st and screenshots."""
import os, subprocess
from emu import *
from pm import *
from btl import *
out = '/tmp/claude-0/-home-user/4de37507-9387-5f1e-bab5-10167305f887/scratchpad/menu'
SHOT = os.environ.get('DISPLAY')
e = Emu('pm-jp.z64', '/dev/shm/pmbot/t1')
if SHOT:
    for i in range(150): e.step(0, 0, 0, 2)
e.load('states/boss_2302_run_menu.st'); e.step(0, 0, 0, 2)
def st(b=0, x=0, y=0, n=1):
    for i in range(n): e.step(b if i == 0 else 0, x, y, 2)
def shot(name):
    if SHOT: subprocess.run(['import', '-window', 'root', '%s/%s.png' % (out, name)], check=True)
st(n=10); st(A, n=20); st(0, 0, -70, 2); st(n=10); shot('t1_jumpmenu'); st(A, n=20); shot('t1_after_charge_select'); st(A, n=10)   # confirm Mario as the target
trace = []
for i in range(3000):
    b = bstate(e)
    if not trace or trace[-1][1] != b: trace.append((i, b))
    if b == 14:
        shot('t1_partner_menu'); st(A, n=20); shot('t1_partner_sub')
        st(A, n=20); shot('t1_partner_target'); st(A, n=10)
        for j in range(120): e.step(A if j % 4 == 0 else 0, 0, 0, 2)
    elif b == 13 and i > 100: break
    elif b == 17: st(A, n=10)
    else: e.step(B, 0, 0, 2)
print('trace', trace)
for i in range(20): e.step(0, 0, 0, 2)
shot('t2_menu')
p = e.u32(BSTATUS + 0xD8)
print('Mario HP', e.s8(PLAYER_DATA + 2), 'FP', e.s8(PLAYER_DATA + 5), 'state', bstate(e))
e.save('states/boss_2302_turn2.st'); e.step(0, 0, 0, 2)
