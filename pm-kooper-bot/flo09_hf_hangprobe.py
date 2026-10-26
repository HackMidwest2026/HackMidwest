"""Find where the flo_09 Happy Flower loop stops: from STATE run the 2-3-1 hits, saving a state before every hit
(states/flo09_hang_hitN.st) and printing a line per hit; a watchdog thread reports when a single 2-frame step
takes longer than 20 s (the emulator stopped returning frames). usage: flo09_hf_hangprobe.py STATE ROUNDS"""
import os, sys, threading, time, faulthandler
from emu import *
from pm import *
from nav import go_to
st, ROUNDS = sys.argv[1], int(sys.argv[2])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/hg%d' % os.getpid())
e.load(st); e.step(0, 0, 0, 2)
last = [time.time(), 'start']
_step = e.step
def step(*a, **k):
    last[0] = time.time(); _step(*a, **k)
e.step = step
def dog():
    while True:
        time.sleep(5)
        if time.time() - last[0] > 20:
            print('WATCHDOG: no frame for 20 s during', last[1], flush=True); os._exit(3)
threading.Thread(target=dog, daemon=True).start()
TREES = {1: -200, 2: 0, 3: 200}; Z = 60
n = 0
def items():
    return sum(1 for i in range(256) if 0x80000000 < e.u32(0x8015AD20 + 4 * i) < 0x80800000 and e.u32(e.u32(0x8015AD20 + 4 * i)) & 1)
for r in range(ROUNDS):
    for t in (2, 3, 1):
        n += 1; last[1] = 'hit %d (tree %d), items %d' % (n, t, items())
        e.save('states/flo09_hang_hit%d.st' % n); e.step(0, 0, 0, 1)
        print(last[1], 'pos', round(player(e)['x']), round(player(e)['z']), 'mode', e.s16(GAME_MODE), flush=True)
        sd = 1 if t == 1 else -1; sx = TREES[t] + 60 * sd
        go_to(e, player(e)['x'], Z, maxf=100, tol=3); go_to(e, sx, Z, maxf=300, tol=3); go_to(e, sx, 10, maxf=100, tol=3)
        for i in range(10): e.step(0, -60 * sd, 0, 2)
        for i in range(3): e.step(0, 0, 0, 2)
        for i in range(2): e.step(B, 0, 0, 2)
        for i in range(25): e.step(0, 0, 0, 2)
        go_to(e, sx, Z, maxf=100, tol=3)
    for i in range(20): e.step(0, 0, 0, 2)
print('done, items', items(), flush=True)
