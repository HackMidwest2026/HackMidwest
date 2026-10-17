"""Simulate the simple ending route for all timing variations: from START, hold up U then right R (very top-right
corner), down D1 frames, A + down held N frames (jump onto the top step and keep walking down), neutral 4, left K
frames, neutral 4, up 40 frames, neutral 6. Report where Mario ends and whether it is in the usable corner.
usage: rta_route.py"""
import math, os, itertools
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rroute')
def in_zone(x, z, y):
    return (abs(y + 20) < 0.5 and -145.5 <= z <= -72 and x >= 871.5 and x <= 871.5 + 0.175 * (-72 - z) and math.hypot(x - 530.8, z + 13) >= 370.4)
L, U_, R_, D_ = stick_for(180, 80), stick_for(270, 80), stick_for(0, 80), stick_for(90, 80)
e.load(os.environ.get('START', 'states/pra01_topright_rj.st')); e.step(0, 0, 0, 2)
for i in range(10): e.step(0, *U_, 2)
for i in range(10): e.step(0, *R_, 2)
for i in range(6): e.step(0, *D_, 2)
e.save('/dev/shm/pmbot/rroute/c.st')
res = {}
for N in (22, 24, 26, 28, 30, 32, 34):
    for K in range(18, 32):
        e.load('/dev/shm/pmbot/rroute/c.st'); e.step(0, 0, 0, 2)
        for i in range(N): e.step(0x80 if i < 12 else 0, *D_, 2)
        for i in range(4): e.step(0, 0, 0, 2)
        for i in range(K): e.step(0, *L, 2)
        for i in range(4): e.step(0, 0, 0, 2)
        p0 = player(e)
        for i in range(40): e.step(0, *U_, 2)
        for i in range(6): e.step(0, 0, 0, 2)
        p = player(e)
        res[(N, K)] = (p0['x'], p0['y'], p0['z'], p['x'], p['y'], p['z'], in_zone(p['x'], p['z'], p['y']) and p['action'] == 0)
for N in (22, 24, 26, 28, 30, 32, 34):
    row = ''.join('Y' if res[(N, K)][6] else '.' for K in range(18, 32))
    zs = res[(N, 18)][2]
    print('down-hold N=%d (Mario at z %.1f before running left): K=18..31 %s' % (N, zs, row))
for (N, K), r in sorted(res.items()):
    if r[6]: print('  N %d K %d: stopped at (%.2f, %.1f, %.2f) -> after up (%.2f, %.1f, %.2f)' % (N, K, *r[:6]))
