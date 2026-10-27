"""pra_18 south->north 'run and wait' setup. After a dismount Lakilester hovers in place for ~32 frames, then starts
following with moveSpeed ~ 0.25 * distance to Mario. So: ride to P (distance R, bearing B from the pillar tip T),
dismount holding toward T, keep running to T, release the stick when Mario is on the clip spot, press C-down on frame K
after the dismount press. Success = riding on the north side. C-down only works on the ground and not mid-spin.
DIAGNOSTIC SETUP as pra18_sn_ring.py. usage: pra18_sn_wait.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
from nav import go_to
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sw%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, 650.0); e.wf32(PLAYER + PS_POS + 8, 45.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 630.0); e.wf32(L['addr'] + 0x40, 45.0)           # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/sw%d_b.st' % os.getpid(); e.save(base)
cur = '/dev/shm/pmbot/sw%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for i in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and q['z'] < 0; e.load(cur); return ok, sp
TARGETS = [(613, 22), (614, 26), (614, 30), (615, 34), (613, 38)]
jobs = list(itertools.product(TARGETS, range(70, 181, 15), range(-10, 191, 15)))[part::nparts]
fo = open(out, 'a'); hits = 0; n = 0
for T, R, B in jobs:
    P = (T[0] + R * math.cos(math.radians(B)), T[1] + R * math.sin(math.radians(B)))
    if P[1] < 14 or P[1] > 140 or P[0] > 735 or P[0] < 515: continue
    e.load(base)
    go_to(e, P[0], P[1], maxf=250, tol=3)
    p = player(e)
    if p['action'] != 33 or math.hypot(p['x'] - P[0], p['z'] - P[1]) > 6: continue
    toward = math.degrees(math.atan2(T[1] - p['z'], T[0] - p['x'])) % 360
    s = st(toward, 80); n += 1
    e.step(D_CBUTTON, *s, 2)
    arrived = False
    for K in range(1, 60):
        q = player(e)
        if not arrived and math.hypot(q['x'] - T[0], q['z'] - T[1]) < 4: arrived = True
        e.step(0, *((0, 0) if arrived else s), 2); q = player(e)
        if q['action'] in (0, 1, 2) and 600 <= q['x'] <= 630 and 10 <= q['z'] <= 45:
            ok, sp = try_clip()
            if ok:
                hits += 1
                rec = {'T': T, 'R': R, 'B': B, 'P': [round(P[0], 1), round(P[1], 1)], 'stick': s, 'K': K, 'arrived': arrived,
                       'at': [round(q['x'], 2), round(q['z'], 2)], 'speed': sp}
                fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec, flush=True)
    if n % 20 == 0: print('tried', n, 'hits', hits, flush=True)
print('done', hits)
