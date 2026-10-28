"""pra_18 statue 1 climb with walking/running momentum, then NEUTRAL (no RAM writes). From the west-door entry
(53,-70): hold UP/DOWN n frames (lane), hold RIGHT at magnitude mag; press A when Mario's x is in [190, 237] (A held
6); release the stick k frames after the first A (or at the second A); second A (tornado) d2 frames after the first;
neutral after. Success: Mario ends standing on the club (y >= 70) or statue top (y >= 99).
usage: pra18_statue1_mom.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/s1m_%d' % os.getpid())
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
b0 = '/dev/shm/pmbot/s1m_%d_b.st' % os.getpid(); e.save(b0)
lanes = [(270, n) for n in range(4, 0, -1)] + [(None, 0)] + [(90, n) for n in range(1, 5)]
pre = {}
for (ld, n), mag in itertools.product(lanes, (80, 40)):
    e.load(b0)
    for i in range(n): e.step(0, *st(ld, 80), 2)
    for i in range(5): e.step(0, 0, 0, 2)
    xs = []
    for i in range(120):
        xs.append(player(e)['x']); e.step(0, *st(0, mag), 2)
    pre[(ld, n, mag)] = [j for j, x in enumerate(xs) if 190 <= x <= 237.5]
jobs = []
for key, js in pre.items():
    for j in js:
        for k in (0, 2, 4, 6, 99):
            for d2 in range(5, 15):
                jobs.append(key + (j, k, d2))
jobs = jobs[part::nparts]
print('jobs', len(jobs), flush=True)
fo = open(out, 'a')
for ld, n, mag, j, k, d2 in jobs:
    e.load(b0)
    for i in range(n): e.step(0, *st(ld, 80), 2)
    for i in range(5): e.step(0, 0, 0, 2)
    for i in range(j): e.step(0, *st(0, mag), 2)
    x0, z0 = player(e)['x'], player(e)['z']
    my = 0
    for i in range(60):
        b = A if (i < 6 or i == d2) else 0
        hold = (i < k) if k != 99 else (i < d2)
        e.step(b, *(st(0, mag) if hold else (0, 0)), 2); my = max(my, player(e)['y'])
    q = player(e)
    if q['y'] >= 70 and q['action'] in (0, 1, 2):
        rec = {'lane': [ld, n], 'mag': mag, 'j': j, 'k': k, 'd2': d2, 'start': [round(x0, 2), round(z0, 2)], 'end': [round(q['x'], 2), round(q['y'], 2), round(q['z'], 2)]}
        fo.write(json.dumps(rec) + '\n'); fo.flush(); print('UP', json.dumps(rec), flush=True)
print('done')
