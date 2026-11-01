"""Build decisive-point states for Jr. Troopa T4 and T5 (DIAGNOSTIC: seeds chosen so the Close Call lands, as planned
in the run). jr_t4_syrup.st: T4 Mario's Maple Syrup target screen (Bombette already bombed). jr_t5_nothing.st: T5
Bombette's Strategies menu, hand on do nothing (Mario already charged)."""
import sys, os
from emu import *
from pm import *
from btl import *
from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jb%d' % os.getpid())
def w(n, b=0, x=0, y=0):
    for i in range(n): e.step(b if i == 0 else 0, x, y if i == 0 else 0, 2)
def until(states, cap=4000, mash=False):
    for f in range(cap):
        if bstate(e) in states: return f
        e.step(A if (mash and f % 2 == 0) else 0, 0, 0, 2)
    raise RuntimeError('state %d' % bstate(e))
hp = lambda: (e.s8(PLAYER_DATA + 2), e.s8(PLAYER_DATA + 5), e.s8(e.u32(BSTATUS + 0xE0) + 0x1B8))
def cc_seed():
    """try seeds until the enemy turn's Close Call lands (Mario HP unchanged); returns after the enemy turn"""
    base = '/dev/shm/pmbot/jb_pre%d.st' % os.getpid(); e.save(base); e.step(0, 0, 0, 1)
    for k in range(1, 60):
        e.load(base); e.step(0, 0, 0, 1); sd = 0x1000 * k + 0x111; e.w32(SEED, sd); e.w32(SEED2, sd)   # DIAGNOSTIC
        h0 = e.s8(PLAYER_DATA + 2)
        yield sd
        if e.s8(PLAYER_DATA + 2) == h0 and bstate(e) == 13: return
# T3: Bomb with a Close Call seed
e.load('states/jr_t3_bomblist.st'); e.step(0, 0, 0, 2)
w(25, A)
for sd in cc_seed():
    w(10, A); until([13, 27, 32], mash=True)
    if bstate(e) == 13: until([13]); 
print('T4 menu', hp(), 'seed %x' % sd)
w(20); w(30, Z); w(25, A); w(10, 0, 0, -70); w(25, A); w(10, A); until([13], mash=True); w(15)   # Bombette Bomb
print('T4 after Bomb', hp()); e.save('states/jr_t4_afterbomb.st')
w(15, 0, 0, 70); w(25, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(25, A); until([17], cap=60)       # items, down 2: Maple Syrup
e.save('states/jr_t4_syrup.st'); print('saved T4 syrup target screen')
for sd in cc_seed():
    w(10, A); until([13, 27, 32])
print('T5 menu', hp(), 'seed %x' % sd)
w(20, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); w(10, A); until([14])                   # Super Charge
w(10); w(15, 0, 0, 70); w(25, A); w(12, 0, 0, -70)                                              # Strategies, hand on do nothing
print('T5 state', bstate(e), hp()); e.save('states/jr_t5_nothing.st')
