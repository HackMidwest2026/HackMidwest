"""pra_18 statue 1 (Clubba statue body x 250-300, z -100..-50, top y 100; club x 234-250, z -89..-61, top y 73-79)
climb with Ultra Boots, starting from the west door (no RAM writes). Mario holds DOWN into the mirror, then RIGHT into
the x=250 wall (bottom-right corner of the west section), then: hammer (B), wait h, hold stick angle a for d1 frames,
A held ha frames, d2 frames later A again (tornado jump), keep holding a. Success: Mario standing on the club
(y >= 70) or on the statue top (y >= 99). usage: pra18_statue1.py PART NPARTS OUT.json"""
import os, sys, json, math, itertools
from emu import *
from pm import *
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/s1_%d' % os.getpid())
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for i in range(40): e.step(0, *st(90, 80), 2)
for i in range(60): e.step(0, *st(0, 80), 2)
for i in range(10): e.step(0, 0, 0, 2)
p = player(e); print('corner', round(p['x'], 2), round(p['z'], 2), flush=True)
base = '/dev/shm/pmbot/s1_%d_b.st' % os.getpid(); e.save(base)
grid = list(itertools.product((270, 285, 300, 315, 330, 345), range(0, 25, 3), (0, 3, 6), (1, 3, 6, 9, 12), range(3, 20)))[part::nparts]
res = []; best = (0,)
for ang, h, d1, ha, d2 in grid:
    e.load(base)
    e.step(B, 0, 0, 2)
    for i in range(h): e.step(0, 0, 0, 2)
    for i in range(d1): e.step(0, *st(ang, 80), 2)
    for i in range(ha): e.step(A, *st(ang, 80), 2)
    for i in range(d2): e.step(0, *st(ang, 80), 2)
    e.step(A, *st(ang, 80), 2)
    my = 0
    for i in range(60):
        e.step(0, *st(ang, 80), 2); q = player(e); my = max(my, q['y'])
    for i in range(20): e.step(0, 0, 0, 2)
    q = player(e)
    r = [ang, h, d1, ha, d2, round(my, 2), round(q['x'], 1), round(q['y'], 1), round(q['z'], 1), q['action']]
    res.append(r)
    if my > best[0]: best = (my, r); print('best', r, flush=True)
    if q['y'] >= 70: print('UP', r, flush=True)
json.dump(res, open(out, 'w')); print('done', best)
