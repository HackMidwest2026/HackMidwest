"""Seed steps and frames across Bowser's first turn (it has a text box), from the partner's turn starting until
Mario's next menu. Text handled by holding B (from offset H frames into the enemy turn) or by tapping A every P frames."""
import sys, os
from emu import *
from pm import *
from btl import *
from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/bt%d' % os.getpid())
def run(seed, mode, par):
    e.load('states/boss_2302_menu.st'); e.step(0, 0, 0, 2)
    for o in (2, 3, 4): e.w8(PLAYER_DATA + o, 99)          # DIAGNOSTIC setup
    e.w32(SEED, seed); e.w32(SEED2, seed)                   # DIAGNOSTIC: chosen seed
    # Mario jump + partner, identical inputs every run
    def st(b=0): e.step(b, 0, 0, 2)
    for j in range(10): st()
    st(A); [st() for j in range(15)]; st(A)
    def until(target):
        for i in range(4000):
            if bstate(e) == target: return
            st(A if i % 20 == 10 else 0)
        raise RuntimeError('never reached state %d' % target)
    until(14)
    st(A); [st() for j in range(15)]
    until(17)
    [st() for j in range(10)]; st(A)
    for i in range(4000):
        if bstate(e) == 21: break
        st()
    # enemy turn: measure from here to Mario's next menu
    s0 = e.u32(SEED); frames = 0; steps = 0; prev = s0
    for i in range(3000):
        if mode == 'B': b = B if i >= par else 0
        elif mode == 'A': b = A if i % par == 0 else 0
        else: b = 0
        e.step(b, 0, 0, 2); frames += 1
        cur = e.u32(SEED); k = 0; x = prev
        while x != cur and k < 400: x = adv(x); k += 1
        steps += k; prev = cur
        if bstate(e) == 13: break
    return frames, steps
seeds = [0x12345678, 0x9abcdef0, 0x0badf00d, 0xdeadbeef, 0x31415926]
for mode, pars in ((sys.argv[1], [int(a) for a in sys.argv[2:]]),):
    for par in pars:
        r = [run(s, mode, par) for s in seeds]
        print('%s %-3s frames %s  seed steps %s' % ('hold B from' if mode == 'B' else 'tap A every', par, sorted(set(x[0] for x in r)), [x[1] for x in r]), flush=True)
