"""tik_23: Lakilester mount (C-down) with his speed forced to S (DIAGNOSTIC: speed write, and Mario placed on a grid
next to the Super Hammer block / invisible wall o102 at x -280). Does the mount put Mario west of the wall
(x < -281, i.e. in the tunnel to tik_24)? usage: tik23_mount_map.py OUT.json"""
import os, sys, json
from emu import *
from pm import *
CD = 0x0400
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mm%d' % os.getpid())
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
res = []; hits = []
for x in (-266, -262, -255, -245, -235):
    for z in (-75, -62, -55, -48, -40, -20, 0, 8, 14, 25, 35):
        for S in (10, 25, 50, 100, 200, 400):
            e.load('states/tik23_westzone.st'); e.step(0, 0, 0, 2)
            e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, -20.0); e.wf32(PLAYER + PS_POS + 8, float(z))
            for i in range(20): e.step(0, 0, 0, 2)
            p0 = player(e)
            e.step(CD, 0, 0, 2)
            for i in range(30):
                if player(e)['action'] != 33:
                    l = laki()
                    if l: e.wf32(l['addr'] + 0x18, float(S))
                e.step(0, 0, 0, 2)
            p = player(e)
            r = (x, z, S, round(p0['x'], 1), round(p0['z'], 1), round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), p['action'])
            res.append(r)
            if p['x'] < -281: hits.append(r); print('CROSSED', r, flush=True)
json.dump(res, open(sys.argv[1], 'w'))
print(len(res), 'tries,', len(hits), 'crossings; min x reached', min(r[5] for r in res))
