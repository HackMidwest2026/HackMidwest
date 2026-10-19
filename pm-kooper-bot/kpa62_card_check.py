"""kpa_62 cardinal-only setup check: up-corner (hold UP 120 frames), hold RIGHT R frames, then the given cardinal
program 'dir:frames ...' (20 neutral frames after each), then the clip sequence (settle 40, C-down, ride 40, B, hold
down, C-down on frame T). Prints the spot after RIGHT, the standing spot and the result.
usage: kpa62_card_check.py STATE R 'left:12 down:12' ...   env: START (x,z), T"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
SX, SZ = (float(v) for v in os.environ.get('START', '-480,-100').split(','))
T = int(os.environ.get('T', '34'))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kck%d' % os.getpid())
base = '/dev/shm/pmbot/kck%d.base' % os.getpid()
e.load(sys.argv[1]); e.step(0, 0, 0, 2); place(e, SX, SZ)
for i in range(120): e.step(0, *CARD['up'], 2)
for i in range(10): e.step(0, 0, 0, 2)
u = player(e)
for i in range(int(sys.argv[2])): e.step(0, *CARD['right'], 2)
for i in range(20): e.step(0, 0, 0, 2)
r = player(e); e.save(base)
print('up corner (%.3f %.3f)  after right (%.3f %.3f)' % (u['x'], u['z'], r['x'], r['z']))
for prog in sys.argv[3:]:
    e.load(base)
    for seg in prog.split():
        d, k = seg.split(':')
        for i in range(int(k)): e.step(0, *CARD[d], 2)
        for i in range(20): e.step(0, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    s = player(e)
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    dn = CARD['down']
    for fr in range(1, T): e.step(0, *dn, 2)
    e.step(0x400, *dn, 2); ok = False
    for f in range(30):
        e.step(0, *dn, 2); q = player(e)
        if f > 18 and q['y'] > 40 and inside_tower(q['x'], q['z']): ok = True; break
    print('%-30s stand (%.3f %.2f) %s' % (prog, s['x'], s['z'], 'CLIP' if ok else 'no'), flush=True)
