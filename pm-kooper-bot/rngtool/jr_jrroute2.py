"""Jr. Troopa route, turn 2 from states/jr_t2_menu.st: Z (Bombette first), Bomb (mash), Mario item (first item:
Whacka's Bump), enemy turn. Saves states/jr_t3_menu.st."""
import sys, os
from emu import *
from pm import *
from btl import *
exec(open('_jrroute.py').read().split("e.load(")[0].split('e = Emu')[0])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jr2%d' % os.getpid())
def w(n, b=0, x=0, y=0):
    for i in range(n): e.step(b if i == 0 else 0, x, y if i == 0 else 0, 2)
def until(states, cap=3000, mash=False):
    for f in range(cap):
        if bstate(e) in states: return f
        e.step(A if (mash and f % 2 == 0) else 0, 0, 0, 2)
    raise RuntimeError('state %d' % bstate(e))
def bomb():
    w(25, A); w(10, 0, 0, -70); w(25, A); w(10, A)
    until([13, 14, 27, 32], mash=True)
e.load('states/jr_t2_menu.st'); e.step(0, 0, 0, 2)
w(30, Z); bomb(); until([13]); w(15)
hp = lambda: (e.s8(PLAYER_DATA + 2), e.s8(PLAYER_DATA + 5), e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8))
print('after Bomb, Mario menu: HP/FP/Jr', hp(), 'state', bstate(e))
w(15, 0, 0, 70); w(25, A); w(25, A)          # items, first item (Whacka's Bump)
for i in range(40):
    if bstate(e) == 17: break
    e.step(0, 0, 0, 2)
print('item target screen?', bstate(e)); w(10, A)
until([13], cap=4000); w(20)
print('T3 menu: HP/FP/Jr', hp())
e.save('states/jr_t3_menu.st')
