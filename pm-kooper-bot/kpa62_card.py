"""kpa_62 RTA chain with cardinal stick directions only (corner notches differ between controllers).
Camera mapping: right = world (+x,-z), down = (+x,+z), left = (-x,+z), up = (-x,-z).
Start: Mario placed with Laki settled at START; hold RIGHT for N frames into the corner between the tower's west face and
the castle wall (a fixed point). Then a program of cardinal holds "dir:frames dir:frames ..." (each hold followed by
REL frames of neutral), settle 40, mount, ride 40, B, hold down, C-down on frame 34.
usage: kpa62_card.py STATE 'left:8 down:4' ...   env: START (x,z), N, REL"""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
SX, SZ = (float(v) for v in os.environ.get('START', '-440,-80').split(','))
N, REL = int(os.environ.get('N', '60')), int(os.environ.get('REL', '15'))
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kcd%d' % os.getpid())
base = '/dev/shm/pmbot/kcd%d.base' % os.getpid()
e.load(sys.argv[1]); e.step(0, 0, 0, 2); place(e, SX, SZ)
for i in range(N): e.step(0, *CARD['right'], 2)
for i in range(10): e.step(0, 0, 0, 2)
c = player(e); print('corner (%.4f %.4f)' % (c['x'], c['z'])); e.save(base)
def run(prog, T=34):
    e.load(base)
    for seg in prog.split():
        d, k = seg.split(':')
        for i in range(int(k)): e.step(0, *CARD[d], 2)
        for i in range(REL): e.step(0, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    s = player(e)
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    dn = CARD['down']
    for fr in range(1, T): e.step(0, *dn, 2)
    e.step(0x400, *dn, 2)
    for f in range(30):
        e.step(0, *dn, 2); q = player(e)
        if f > 18 and q['y'] > 40 and inside_tower(q['x'], q['z']): return s, True
    return s, False
if __name__ == '__main__':
    print('sticks', CARD)
    for prog in sys.argv[2:]:
        s, ok = run(prog)
        print('%-28s stand (%.3f %.2f) %s' % (prog, s['x'], s['z'], 'CLIP' if ok else 'no'), flush=True)
