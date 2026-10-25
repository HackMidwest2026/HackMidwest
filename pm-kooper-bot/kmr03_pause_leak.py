"""Hammer-block leak in kmr_03 combined with pausing: for each plan, hit the Hammer2 block 10 times from the left side;
after each hit wait D steps, open the pause menu (Start), wait P steps, close it, wait for the shiver to end.
Reports general-heap bytes leaked per hit and the leaked block sizes.  usage: kmr03_pause_leak.py"""
import os
from emu import *
from pm import *
from heapsim import Heap

e = Emu('pm-jp.z64', '/dev/shm/pmbot/pl%d' % os.getpid())
def snap():
    h = Heap.from_emu(e)
    return {a + 0x10: ln for a, nxt, ln, al, mid in h.walk() if al}
def run(D, P):
    e.load('states/kmr03_hammer2_left.st'); e.step(0, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    before = snap()
    for k in range(10):
        for i in range(2): e.step(B, 0, 0, 2)
        for i in range(D): e.step(0, 0, 0, 2)
        if P is not None:
            e.step(START, 0, 0, 2)
            for i in range(P): e.step(0, 0, 0, 2)
            e.step(START, 0, 0, 2)
        for i in range(40): e.step(0, 0, 0, 2)
    for i in range(60): e.step(0, 0, 0, 2)
    after = snap()
    new = {a: ln for a, ln in after.items() if a not in before}
    sizes = {}
    for ln in new.values(): sizes[ln] = sizes.get(ln, 0) + 1
    return sum(ln + 0x10 for ln in new.values()) - sum(ln + 0x10 for a, ln in before.items() if a not in after), sizes
print('no pause      :', run(0, None), flush=True)
for D in (0, 3, 6, 10):
    for P in (10, 30):
        print('pause at +%2d steps, %2d steps paused:' % (D, P), run(D, P), flush=True)
