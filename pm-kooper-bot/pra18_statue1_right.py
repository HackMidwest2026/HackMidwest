"""pra_18 statue 1 climb, 'hold RIGHT from the door' version (no RAM writes). From the west-door entry (53,-70), hold
RIGHT the whole time (Mario walks under the club, x 234-250 / z -89..-61 / underside y 51, toward the statue body at
x 250); A at frame j (A held ha frames), second A d2 frames later (Ultra Boots tornado jump). Logs the highest y and
whether Mario ends on the club (y >= 70) or the statue top (y >= 99). usage: pra18_statue1_right.py PART NPARTS OUT.json"""
import os, sys, json, math, itertools
from emu import *
from pm import *
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/s1r_%d' % os.getpid())
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/s1r_%d_b.st' % os.getpid(); e.save(base)
R = st(0, 80)
grid = list(itertools.product(range(0, 61), range(1, 13), range(3, 19)))[part::nparts]
res = []; best = (0,)
for j, ha, d2 in grid:
    e.load(base)
    for i in range(j): e.step(0, *R, 2)
    x0 = player(e)['x']
    for i in range(ha): e.step(A, *R, 2)
    for i in range(d2 - ha if d2 > ha else 0): e.step(0, *R, 2)
    e.step(A, *R, 2)
    my = 0
    for i in range(50):
        e.step(0, *R, 2); q = player(e); my = max(my, q['y'])
    for i in range(15): e.step(0, 0, 0, 2)
    q = player(e)
    r = [j, ha, d2, round(x0, 1), round(my, 2), round(q['x'], 1), round(q['y'], 1), round(q['z'], 1), q['action']]
    res.append(r)
    if my > best[0]: best = (my, r); print('best', r, flush=True)
    if q['y'] >= 70: print('UP', r, flush=True)
json.dump(res, open(out, 'w')); print('done', best)
