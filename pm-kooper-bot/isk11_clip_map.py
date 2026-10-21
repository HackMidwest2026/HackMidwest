"""isk_11 clip map: which mount speeds send Mario to isk_19 from where (exploration: Mario's position and Laki's
moveSpeed are RAM writes). For every grid point on an active floor that Mario can stand on (not the pedestal tops):
  1. cheap pass: for each speed S, C-down with Laki's moveSpeed held at S until the mount reads it, and record the
     landing point (Laki moveToPos). A candidate is a landing point with no floor below it or with the highest floor
     below it more than 40 units under Mario's floor.
  2. candidates only: replay the mount and steer toward the isk_19 exit floor (collider 13, aim 220,532) for 150 game
     frames; a hit is the map changing to isk_19 (map index 16).
Writes one JSON line per point: {x, z, y, floor, land: [[S, lx, lz], ...], hits: [S, ...]}.
usage: isk11_clip_map.py PART NPARTS OUT.jsonl   env XR, ZR, SR (start,stop,step)"""
import json, math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
PART, NP, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rng = lambda k, d: (lambda a, b, c: [a + i * c for i in range(int(round((b - a) / c)) + 1)])(*(float(v) for v in os.environ.get(k, d).split(',')))
XS, ZS, SS = rng('XR', '-340,440,8'), rng('ZR', '370,680,8'), rng('SR', '4,160,4')
d = json.load(open('isk11_collision.json'))
floors = [(c['id'], t['v']) for c in d['colliders'] if not (c['flags'] & 0x7FFFFE00) for t in c['tris'] if t['n'][1] > 0.7]
def floors_at(x, z):
    res = []
    for cid, v in floors:
        (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = v
        den = (z2 - z3) * (x1 - x3) + (x3 - x2) * (z1 - z3)
        if abs(den) < 1e-9: continue
        a = ((z2 - z3) * (x - x3) + (x3 - x2) * (z - z3)) / den
        b = ((z3 - z1) * (x - x3) + (x1 - x3) * (z - z3)) / den
        if min(a, b, 1 - a - b) < -1e-6: continue
        res.append((a * y1 + b * y2 + (1 - a - b) * y3, cid))
    return sorted(res, reverse=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/icm%d' % os.getpid())
e.load('states/isk11_laki_ready.st'); e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/icm%d.st' % os.getpid(); e.save(base)
def setup(x, Y, z):
    e.load(base)
    lk = [q for q in npcs(e) if q['id'] == -4][0]['addr']
    e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, Y + 2); e.wf32(PLAYER + PS_POS + 8, z)
    e.wf32(lk + 0x38, x - 20); e.wf32(lk + 0x3C, Y + 20); e.wf32(lk + 0x40, z)
    for i in range(4): e.step(0, 0, 0, 2)
    return lk
def mount(lk, S):
    e.wf32(lk + 0x18, S); e.step(D_CBUTTON, 0, 0, 2)
    for i in range(20):
        if e.u8(PLAYER + PS_ACTION) == 33: return (e.f32(lk + 0x60), e.f32(lk + 0x68))
        e.wf32(lk + 0x18, S); e.step(0, 0, 0, 2)
    return None
fo = open(out, 'a'); npts = nhits = 0
for (x, z) in [(x, z) for x in XS for z in ZS][PART::NP]:
    fl = floors_at(x, z)
    if not fl or fl[0][0] > -460: continue
    Y, cid = fl[0]
    lk = setup(x, Y, z); p = player(e)
    if p['action'] != 0 or abs(p['y'] - Y) > 3 or abs(p['x'] - x) > .5 or abs(p['z'] - z) > .5: continue
    e.save(base + '.pt')
    land, cand = [], []
    for S in SS:
        e.load(base + '.pt'); lk = [q for q in npcs(e) if q['id'] == -4][0]['addr']
        t = mount(lk, S)
        if t is None: continue
        land.append([S, round(t[0], 1), round(t[1], 1)])
        below = [f for f in floors_at(t[0], t[1]) if f[0] <= Y + 5]
        if not below or below[0][0] < Y - 40: cand.append(S)
    hits = []
    for S in cand:
        e.load(base + '.pt'); lk = [q for q in npcs(e) if q['id'] == -4][0]['addr']
        if mount(lk, S) is None: continue
        for f in range(150):
            q = player(e); st = stick_for(math.degrees(math.atan2(532 - q['z'], 220 - q['x'])) % 360, 80)
            e.step(0, st[0], st[1], 2)
            if where(e)[1] == 16: hits.append(S); break
    npts += 1; nhits += len(hits)
    fo.write(json.dumps({'x': x, 'z': z, 'y': round(Y, 1), 'floor': cid, 'land': land, 'cand': cand, 'hits': hits}) + '\n'); fo.flush()
print('done part', PART, npts, 'points', nhits, 'hits')
