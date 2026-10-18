"""pra_03: C-down mounts at given spots with Laki's speed forced to very high values; prints the mount trace end
(riding position) and whether Mario ends outside the room. usage: pra03_probe.py"""
import os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p3p')
w = '/dev/shm/pmbot/p3p'
e.load('states/pra03_e1.st'); e.step(0, 0, 0, 2); e.save(w + '/b.st')
def mount(x, z, S, ride=25):
    e.load(w + '/b.st')
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, z)
    for i in range(12): e.step(0, 0, 0, 2)
    e.step(CD, 0, 0, 2)
    for i in range(ride):
        for n in npcs(e):
            if n['id'] == -4 and player(e)['action'] != 33: e.wf32(n['addr'] + 0x18, float(S))
        e.step(0, 0, 0, 2)
    p = player(e)
    return p['x'], p['y'], p['z'], p['action'], where(e)[:2]
if __name__ == '__main__':
    for x, z in ((-240, -10), (240, -10), (240, -140), (-240, -140), (0, -10), (0, -140), (-100, -75)):
        for S in (3000, 10000, 1e5, 1e6, 1e7):
            r = mount(float(x), float(z), S)
            out = not (-251 <= r[0] <= 251 and -151 <= r[2] <= 1)
            print('(%4d, %4d) S %8g -> (%.1f, %.1f, %.1f) act %d map %s %s' % (x, z, S, *r, 'OUTSIDE' if out else ''))
