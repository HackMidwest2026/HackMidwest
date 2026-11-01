import sys, os
from emu import *
from pm import *
from btl import *
from rngsim import *
src = open('_jrbuild.py').read()
exec(src[:src.index('# T3: Bomb with a Close Call seed')].split('e = Emu(')[0])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jbb%d' % os.getpid())
exec(src[src.index('def w('):src.index('# T3: Bomb with a Close Call seed')])
e.load('states/jr_t4_itemlist.st'); e.step(0, 0, 0, 2)
w(10, 0, 0, -70); w(10, 0, 0, -70); w(25, A); until([17], cap=60)
e.save('states/jr_t4_syrup.st'); e.step(0, 0, 0, 1); print('saved T4 syrup target screen', hp())
for sd in cc_seed():
    w(10, A); until([13, 27, 32])
print('T5 menu', hp(), 'seed %x' % sd)
w(20); w(12, 0, 0, -70); w(22, A); w(10, 0, 0, -70); w(10, 0, 0, -70); w(20, A); w(10, A); until([14])   # wheel on Items -> Jump, Super Charge
print('FP after charge', hp())
w(10); w(15, 0, 0, 70); w(25, A); w(12, 0, 0, -70)                                                      # Bombette Strategies, hand on do nothing
print('T5 state', bstate(e), hp()); e.save('states/jr_t5_nothing.st')
