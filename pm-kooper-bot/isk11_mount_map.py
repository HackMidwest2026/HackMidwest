"""isk_11 (Stone Puzzle Room, puzzle unsolved): where does a Lakilester mount at speed S put Mario? Mario is placed on
an active floor at (x, z) (exploration: placement and Laki's moveSpeed are RAM writes), C-down; Laki's moveSpeed is
held at S until the mount starts (RIDE_STATE_MOUNT_1 reads it to build moveToPos: 4 test moves of S units at yaw
0/90/180/270 from Mario). Then 120 game frames; records Laki's moveToPos and Mario's lowest y. A hit = Mario ends
below -700 (under the -520/-600 floors, i.e. on the hidden staircase or the -910 floor).
usage: isk11_mount_map.py PART NPARTS OUT.jsonl   env XR, ZR, SR (start,stop,step)"""
import json, math, os, sys
from emu import *
from pm import *
PART, NP, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rng = lambda k, d: (lambda a, b, c: [a + i * c for i in range(int(round((b - a) / c)) + 1)])(*(float(v) for v in os.environ.get(k, d).split(',')))
XS, ZS, SS = rng('XR', '-340,440,8'), rng('ZR', '380,680,8'), rng('SR', '4,80,4')
d = json.load(open('isk11_collision.json'))
floors = []
for c in d['colliders']:
    if c['flags'] & 0x7FFFFE00: continue
    for t in c['tris']:
        if t['n'][1] > 0.7: floors.append((c['id'], t['v']))
def floor_at(x, z):
    best = None
    for cid, v in floors:
        (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = v
        den = (z2 - z3) * (x1 - x3) + (x3 - x2) * (z1 - z3)
        if abs(den) < 1e-9: continue
        a = ((z2 - z3) * (x - x3) + (x3 - x2) * (z - z3)) / den
        b = ((z3 - z1) * (x - x3) + (x1 - x3) * (z - z3)) / den
        cc = 1 - a - b
        if min(a, b, cc) < 0: continue
        y = a * y1 + b * y2 + cc * y3
        if best is None or y > best[0]: best = (y, cid)
    return best
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ikm%d' % os.getpid())
e.load('states/isk11_laki_ready.st'); e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/ikm%d.st' % os.getpid(); e.save(base)
fo = open(out, 'a'); n = hits = 0
pts = [(x, z) for x in XS for z in ZS]
for (x, z) in pts[PART::NP]:
    f = floor_at(x, z)
    if f is None or f[0] > -460: continue
    Y = f[0]; row = []
    for S in SS:
        e.load(base)
        lk = [q for q in npcs(e) if q['id'] == -4][0]['addr']
        e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, Y + 2); e.wf32(PLAYER + PS_POS + 8, z)
        e.wf32(lk + 0x38, x - 20); e.wf32(lk + 0x3C, Y + 20); e.wf32(lk + 0x40, z)
        for i in range(4): e.step(0, 0, 0, 2)
        p = player(e)
        if p['action'] != 0 or abs(p['y'] - Y) > 3 or abs(p['x'] - x) > .5 or abs(p['z'] - z) > .5: break
        e.wf32(lk + 0x18, S); e.step(D_CBUTTON, 0, 0, 2); t = None
        for i in range(20):
            if e.u8(PLAYER + PS_ACTION) == 33: t = (e.f32(lk + 0x60), e.f32(lk + 0x64), e.f32(lk + 0x68)); break
            e.wf32(lk + 0x18, S); e.step(0, 0, 0, 2)
        if t is None: continue
        low = 1e9
        for i in range(120):
            e.step(0, 0, 0, 2); low = min(low, e.f32(PLAYER + PS_POS + 4))
        n += 1; p = player(e)
        hit = low < -700 and (where(e)[1] != 10 or -950 < p["y"] < -600)
        hits += hit
        row.append([S, round(t[0], 1), round(t[2], 1), round(low, 1), round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), where(e)[1], int(hit)])
    if row: fo.write(json.dumps({'x': x, 'z': z, 'y': round(Y, 1), 'floor': f[1], 'r': row}) + '\n'); fo.flush()
print('done part', PART, n, 'mounts', hits, 'down')
