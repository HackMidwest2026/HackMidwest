"""Hallway scene (kkj_13) with B held: the exact per-frame schedule of draws beyond the per-frame step and the coin.
Frames counted from loading states/kkj13_e0.st (the scene starts right away there). The minimum over 10 seeds per frame
removes the coin draw (which falls on different frames for different seeds). DIAGNOSTIC: random seed written per run."""
import os, sys, random
os.chdir('/tmp/claude-0/pm/bot1'); sys.path.insert(0, '.')
from emu import *; from pm import *; from rngsim import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/zwsched')
for i in range(60): e.step(0, 0, 0, 2)
rnd = random.Random(11); per = []
for n in range(10):
    e.load('states/kkj13_e0.st'); e.step(0, 0, 0, 2)
    s = rnd.getrandbits(32); e.w32(SEED, s)            # DIAGNOSTIC: random seed
    d = {}
    for f in range(400):
        prev = e.u32(SEED); e.step(B, 0, 0, 2); cur = e.u32(SEED)
        k = 0; t = prev
        while t != cur and k < 20000: t = adv(t); k += 1
        if k > 1: d[f] = k - 1
        if e.s16(GAME_MODE) not in (GM_WORLD, GM_CHANGE_MAP, GM_ENTER_WORLD): break
    per.append((f, d))
frames = sorted(set(k for _, d in per for k in d))
sched = {}
for f in frames:
    m = min(d.get(f, 0) for _, d in per)
    if m > 0: sched[f] = m
print('battle at frame', sorted(set(p[0] for p in per)))
print('schedule', sched, 'total', sum(sched.values()))
