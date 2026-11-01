import sys, os
from emu import *
from pm import *
from btl import *
from rngsim import *
src = open('_jrbuild.py').read()
e = Emu('pm-jp.z64', '/dev/shm/pmbot/jbc%d' % os.getpid())
exec(src[src.index('def w('):src.index('# T3: Bomb with a Close Call seed')])
e.load('states/jr_t5_nothing.st'); e.step(0, 0, 0, 2)
for sd in cc_seed():
    w(10, A); until([13, 27, 32])
print('T6 menu', hp(), 'seed %x' % sd)
w(20); w(22, A); w(10, 0, 0, -70); w(25, A); until([17], cap=60)        # wheel on Jump: A, down 1 = Power Bounce, A -> target screen
e.save('states/jr_t6_pb_target.st'); e.step(0, 0, 0, 1); print('saved T6 PB target', bstate(e), hp())
