"""pra_18 statue 2 climb (user's method): Mario in the corridor's bottom-right corner (statue 2 west face x=450 /
corridor south wall z=-50), hammer, hold up-right, then A, A (tornado jump with Ultra Boots) still holding up-right.
Scans the timing: hammer -> hold delay h, first A at d1, second press (A or Z) d2 frames later, stick angle.
DIAGNOSTIC SETUP: Mario placed in the corridor at (400,-75) (the corridor can't be reached without passing statue 1);
everything after is real input. Success = Mario standing on statue 2's top (y >= 99) or on its club (y >= 70).
usage: pra18_statue2.py OUT.json"""
import os, sys, json, math, itertools
from emu import *
from pm import *
e = Emu('pm-jp.z64', '/dev/shm/pmbot/st2_%d' % os.getpid())
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 400.0); e.wf32(PLAYER + PS_POS + 8, -75.0)                    # DIAGNOSTIC
for n in npcs(e):
    if n['id'] == -4: e.wf32(n['addr'] + 0x38, 370.0); e.wf32(n['addr'] + 0x40, -75.0)  # DIAGNOSTIC (Laki along)
for i in range(30): e.step(0, 0, 0, 2)
for i in range(40): e.step(0, *st(45, 80), 2)          # down-right into the corner
for i in range(10): e.step(0, 0, 0, 2)
p = player(e); print('corner', p, flush=True)
base = '/dev/shm/pmbot/st2_b%d.st' % os.getpid(); e.save(base)
res = []; best = (0,)
PART, NP = int(os.environ.get('PART', '0')), int(os.environ.get('NP', '1'))
grid = list(itertools.product((315, 300, 330), range(0, 25, 3), (0, 3, 6), (1, 3, 6, 9, 12), range(4, 20)))[PART::NP]
for ang, h, d1, ha, d2 in grid:
    e.load(base)
    e.step(B, 0, 0, 2)                                   # hammer
    for i in range(h): e.step(0, 0, 0, 2)
    for i in range(d1): e.step(0, *st(ang, 80), 2)       # start holding up-right
    for i in range(ha): e.step(A, *st(ang, 80), 2)       # jump, A held ha frames
    for i in range(d2): e.step(0, *st(ang, 80), 2)
    e.step(A, *st(ang, 80), 2)                           # second A: tornado jump
    my = 0
    for i in range(60):
        e.step(0, *st(ang, 80), 2); q = player(e); my = max(my, q['y'])
    for i in range(20): e.step(0, 0, 0, 2)
    q = player(e)
    r = [ang, h, d1, ha, d2, round(my, 2), round(q['x'], 1), round(q['y'], 1), round(q['z'], 1), q['action']]
    res.append(r)
    if my > best[0]: best = (my, r); print('best', r, flush=True)
    if q['y'] >= 70: print('UP', r, flush=True)
json.dump(res, open('/tmp/claude-0/pm/p18/statue2_%d.json' % PART, 'w')); print('done', best)
