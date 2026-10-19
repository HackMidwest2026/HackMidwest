"""kpa_62 cardinal-only setups: frame-count tolerance of each move. A program is a list of moves from the up-corner
(hold UP into the north-west corner): walk:DIR:k, jump:DIR:k (A + DIR held k frames), spin:DIR:k, hold:DIR:k. For each
move, its frame count is varied by -3..+3 with the others fixed; prints which variations still clip.
usage: kpa62_card_tol.py STATE 'walk:right:30 walk:left:12 walk:down:12' ..."""
import os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
from kpa62_tower import inside_tower
from kpa62_place import place
CARD = {'right': stick_for(0, 80), 'down': stick_for(90, 80), 'left': stick_for(180, 80), 'up': stick_for(270, 80)}
A, Z = 0x0080, 0x0020
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/kct%d' % os.getpid())
base = '/dev/shm/pmbot/kct%d.base' % os.getpid()
e.load(sys.argv[1]); e.step(0, 0, 0, 2); place(e, -480.0, -100.0)
for i in range(120): e.step(0, *CARD['up'], 2)
for i in range(10): e.step(0, 0, 0, 2)
e.save(base)
def do(kind, d, k):
    if kind in ('walk', 'hold'):
        for i in range(k): e.step(0, *CARD[d], 2)
    elif kind == 'spin':
        e.step(Z, *CARD[d], 2)
        for i in range(k - 1): e.step(0, *CARD[d], 2)
    else:
        e.step(A, *CARD[d], 2)
        for i in range(k): e.step(A, *CARD[d], 2)
        for i in range(30 - k): e.step(0, 0, 0, 2)
    for i in range(20): e.step(0, 0, 0, 2)
def run(moves):
    e.load(base)
    for m in moves: do(*m)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x400, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    e.step(0x40, 0, 0, 2)
    dn = CARD['down']
    for fr in range(1, 34): e.step(0, *dn, 2)
    e.step(0x400, *dn, 2)
    for f in range(30):
        e.step(0, *dn, 2); q = player(e)
        if f > 18 and q['y'] > 40 and inside_tower(q['x'], q['z']): return True
    return False
for prog in sys.argv[2:]:
    moves = [(s.split(':')[0], s.split(':')[1], int(s.split(':')[2])) for s in prog.split()]
    print(prog, 'CLIP' if run(moves) else 'no')
    for i, (kind, d, k) in enumerate(moves):
        ok = [dk for dk in range(-3, 4) if k + dk >= 0 and run(moves[:i] + [(kind, d, k + dk)] + moves[i + 1:])]
        print('   %s:%s: works for %s' % (kind, d, [k + dk for dk in ok]), flush=True)
