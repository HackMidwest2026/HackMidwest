"""pra_18 statue 2 climb, fine search around the best coarse result (y 81.35: hammer, wait h=9, hold up-right 6 frames,
A held 6, tornado A 4-5 frames later). Varies stick angle and every timing, tracks the frames Mario stands at y >= 70
(on the club, top at 73-79) and then tries a second jump (A, held) from there to reach the statue top (y 100).
DIAGNOSTIC SETUP as pra18_statue2.py (Mario placed in the corridor; the corridor needs statue 1 passed first).
usage: pra18_statue2b.py PART NPARTS"""
import os, sys, json, math, itertools
from emu import *
from pm import *
part, nparts = int(sys.argv[1]), int(sys.argv[2])
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sb%d' % os.getpid())
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 400.0); e.wf32(PLAYER + PS_POS + 8, -75.0)                    # DIAGNOSTIC
for n in npcs(e):
    if n['id'] == -4: e.wf32(n['addr'] + 0x38, 370.0); e.wf32(n['addr'] + 0x40, -75.0)  # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
for i in range(40): e.step(0, *st(45, 80), 2)
for i in range(10): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/sb%d_b.st' % os.getpid(); e.save(base)
grid = list(itertools.product(range(295, 340, 5), range(5, 14), range(3, 10), range(3, 10), range(2, 8)))[part::nparts]
best = (0,); found = []
for ang, h, d1, ha, d2 in grid:
    e.load(base)
    e.step(B, 0, 0, 2)
    for i in range(h): e.step(0, 0, 0, 2)
    for i in range(d1): e.step(0, *st(ang, 80), 2)
    for i in range(ha): e.step(A, *st(ang, 80), 2)
    for i in range(d2): e.step(0, *st(ang, 80), 2)
    e.step(A, *st(ang, 80), 2)
    my = 0; on = None
    for i in range(70):
        e.step(0, *st(ang, 80), 2); q = player(e); my = max(my, q['y'])
        if q['y'] >= 70 and q['action'] in (0, 1, 2, 10) and on is None: on = (i, round(q['x'], 1), round(q['y'], 1), round(q['z'], 1), q['action'])
    q = player(e)
    r = [ang, h, d1, ha, d2, round(my, 2), on, round(q['x'], 1), round(q['y'], 1), round(q['z'], 1), q['action']]
    if my > best[0]: best = (my, r); print('best', r, flush=True)
    if on or q['y'] >= 70:
        print('ON', r, flush=True); found.append(r)
json.dump(found, open('/tmp/claude-0/pm/p18/statue2b_%d.json' % part, 'w')); print('done', best, len(found))
