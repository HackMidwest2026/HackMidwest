"""pra_02 strip: exact x window (step 0.25) at several z and forced speeds. usage: pra02_strip_fine.py"""
import os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p2f')
w = '/dev/shm/pmbot/p2f'
e.load('states/pra02_back_pillar.st'); e.step(0, 0, 0, 2); e.save(w + '/b.st')
def clip(x, z, S):
    e.load(w + '/b.st')
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, z)
    for i in range(12): e.step(0, 0, 0, 2)
    px = player(e)['x']
    e.step(CD, 0, 0, 2)
    for i in range(40):
        for n in npcs(e):
            if n['id'] == -4 and player(e)['action'] != 33: e.wf32(n['addr'] + 0x18, float(S))
        e.step(0, 0, 0, 2)
    return player(e)['z'] > 1, px
def wall_min():
    """minimum forced speed (step 2) that clips with Mario against the right wall (x 987), for z -15..-210"""
    for z in range(-15, -215, -10):
        ok = [S for S in range(196, 262, 2) if clip(987.0, float(z), S)[0]]
        print('wall x 987, z %4d: min clip speed %s  (clips at %d of %d tested speeds 196..260)' % (z, ok[0] if ok else '-', len(ok), len(range(196, 262, 2))), flush=True)


xs = [970 + 0.25 * i for i in range(69)]
if os.environ.get('WALL'): wall_min(); raise SystemExit
for z in (-20.0, -45.0, -65.0, -100.0, -140.0):
    for S in (180, 230, 300):
        row = ''.join('Y' if clip(x, z, S)[0] else '.' for x in xs)
        ok = [x for x, c in zip(xs, row) if c == 'Y']
        print('z %5.0f S %d: x %s  %s' % (z, S, ('%.2f..%.2f' % (min(ok), max(ok))) if ok else '-', row), flush=True)
