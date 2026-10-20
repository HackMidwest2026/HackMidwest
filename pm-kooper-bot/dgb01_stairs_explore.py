"""Explore the broken stairs (debris slab c44, plank c45, standing railing chunk) on dgb_01 2F east.
Tubba is parked far away every frame (exploration only). Mario is teleported to grid spots on the slab and the
walkway around it, settles, then tries: hold DIR the whole time, walk k game frames, jump (A held), optional
tornado (second A t game frames after the first). Records peak y and where Mario ends 70 game frames later.
usage: dgb01_stairs_explore.py PART NPARTS OUT.jsonl"""
import json, sys
from emu import *
from pm import *

part, nparts, outp = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/stairs%d' % part)
e.load('states/dgb01_e4_ctrl.st')
e.w8(PLAYER_DATA, 2)
for p in (1, 2, 3, 8): e.w8(PLAYER_DATA + 0x14 + 8 * p, 1)
tubba = [n for n in npcs(e) if n['id'] == 4][0]['addr']
def park():
    e.wf32(tubba + 0x38, 0.0); e.wf32(tubba + 0x3C, -1000.0); e.wf32(tubba + 0x40, 0.0)
def step(b, x, y, n=1):
    for i in range(n):
        park(); e.step(b, x, y, 1)
for i in range(4): step(0, 0, 0)
base = '/dev/shm/pmbot/stairs_base%d.st' % part
e.save(base)
D = {'u': (0, 80), 'd': (0, -80), 'l': (-80, 0), 'r': (80, 0),
     'ul': (-56, 56), 'ur': (56, 56), 'dl': (-56, -56), 'dr': (56, -56)}
spots = [(x, z) for x in range(5, 260, 15) for z in range(-70, 101, 15)]
spots = spots[part::nparts]
f = open(outp, 'a')
seen = set()
for sx, sz in spots:
    e.load(base)
    step(0, 0, 0)
    e.wf32(PLAYER + PS_POS, sx); e.wf32(PLAYER + PS_POS + 4, 360.0); e.wf32(PLAYER + PS_POS + 8, sz)
    step(0, 0, 0, 40)
    p = player(e)
    key = (round(p['x']), round(p['y']), round(p['z']))
    if p['y'] < 200 or p['action'] not in (0, 1, 2) or key in seen:
        continue
    seen.add(key)
    spot = '/dev/shm/pmbot/stairs_spot%d.st' % part
    e.step(0, 0, 0, 1); e.save(spot)
    for dn, (dx, dy) in D.items():
        for k in (0, 3, 6):
            for t in (None, 6, 7, 8, 9):
                e.load(spot)
                maxy = -1e9; traj = []
                step(0, dx, dy, 2 * k)
                hold = 2 * (t - 1) if t else 30
                for i in range(hold):
                    step(A, dx, dy); maxy = max(maxy, player(e)['y'])
                if t:
                    step(0, dx, dy, 2)
                    step(A, dx, dy, 2)
                for i in range(140):
                    step(0, dx, dy)
                    q = player(e); maxy = max(maxy, q['y'])
                    if i % 10 == 0: traj.append((round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)))
                q = player(e)
                f.write(json.dumps({'spot': key, 'dir': dn, 'k': k, 't': t, 'maxy': round(maxy, 2),
                                    'end': (round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)), 'act': q['action'],
                                    'traj': traj}) + '\n')
    f.flush()
print('done part', part, len(seen), 'spots')
