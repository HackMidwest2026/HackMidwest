"""dgb_01 (intact): how fast can Laki be at the remount in normal play? From several spots: mount, ride 40, dismount (B),
then run (or spin-dash, Z on the landing frame) in a cardinal direction; for every C-down frame 1..70 after the B,
read Laki's moveSpeed when the mount reads it (the frame Mario's action becomes RIDE). Prints the best per setup.
usage: dgb01_max_speed.py STATE"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/dms%d' % os.getpid())
tmp = '/dev/shm/pmbot/dms%d' % os.getpid()
e.load(sys.argv[1]); e.step(0, 0, 0, 2); e.save(tmp + '.st0')
best_all = 0
for (sx, sz) in [(-300, 300), (0, 0), (300, -300), (-350, -100), (200, 300)]:
    for D in CARD:
        for spin in (False, True):
            e.load(tmp + '.st0'); place(e, float(sx), float(sz), y=0.0)
            e.step(0x400, 0, 0, 2)
            for i in range(40): e.step(0, 0, 0, 2)
            e.step(0x40, 0, 0, 2); e.save(tmp + '.b')
            best = (0, None)
            for T in range(1, 71):
                e.load(tmp + '.b')
                for f in range(1, T): e.step(0x20 if (spin and f == 15) else 0, *CARD[D], 2)
                e.step(0x400, *CARD[D], 2)
                a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
                for i in range(20):
                    if e.u8(PLAYER + PS_ACTION) == 33: break
                    e.step(0, 0, 0, 2)
                S = e.f32(a + 0x18)
                if S > best[0]: best = (S, T)
            best_all = max(best_all, best[0])
            print('start (%d, %d) %-5s %s: best mount speed %.1f (C-down on frame %s)' % (sx, sz, D, 'spin' if spin else 'run ', best[0], best[1]), flush=True)
print('highest mount speed found:', round(best_all, 1))
