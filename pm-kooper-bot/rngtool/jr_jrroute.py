"""Play the Jr. Troopa route in the emulator turn by turn and save a state at each turn's menu.
Turn 1: Mario Super Charge, Bombette Bomb (mash). Saves states/jr_t2_menu.st."""
import sys, os
from emu import *
from pm import *
from btl import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jr%d' % os.getpid())
def w(n, b=0, x=0, y=0):
    for i in range(n): e.step(b if i == 0 else 0, x, y if i == 0 else 0, 2)
def until(states, cap=3000, mash=False):
    for f in range(cap):
        if bstate(e) in states: return f
        e.step(A if (mash and f % 2 == 0) else 0, 0, 0, 2)
    raise RuntimeError('state %d' % bstate(e))
def mario_charge():
    w(15, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); w(10, A)
def bomb():
    w(25, A); w(10, 0, 0, -70); w(25, A); w(10, A)            # moves, down 1 (Bomb), A, target A
    until([13, 14, 27, 32], mash=True)
e.load(sys.argv[1] if len(sys.argv) > 1 else 'states/boss_0207_route_menu.st'); e.step(0, 0, 0, 2)
mario_charge(); until([14]); w(10); bomb(); until([13]); w(20)
print('T2 menu: Mario HP', e.s8(PLAYER_DATA + 2), 'FP', e.s8(PLAYER_DATA + 5), 'Jr HP', e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8))
e.save('states/jr_t2_menu.st')
