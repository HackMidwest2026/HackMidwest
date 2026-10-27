"""pra_18 north->south 'run and wait' setup (see pra18_sn_wait.py). The clip needs speed ~616-x (1-2 window) at the
spot west of the east pillar, so Lakilester must be ~4*(616-x) units away when he starts following ~32 frames after the
dismount press. Ride to P (distance R, bearing B from target T), dismount holding toward T, optionally spin (Z) on
landing, run to T, release, C-down on frame K. DIAGNOSTIC SETUP: Mario placed on foot at (600,-60) on the north side,
mounts and rides 40 frames (resets Laki's follow history). usage: pra18_ns_wait.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
from nav import go_to
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/nw%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 600.0); e.wf32(PLAYER + PS_POS + 8, -60.0)                     # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 580.0); e.wf32(L['addr'] + 0x40, -60.0)          # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/nw%d_b.st' % os.getpid(); e.save(base)
cur = '/dev/shm/pmbot/nw%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for i in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and q['z'] > 0; e.load(cur); return ok, sp
TARGETS = [(574, -15), (572, -18), (570, -15), (566, -18), (562, -15), (558, -18)]
jobs = list(itertools.product(TARGETS, range(120, 261, 15), range(180, 361, 15), (0, 1)))[part::nparts]
fo = open(out, 'a'); hits = 0; n = 0
for T, R, B, spin in jobs:
    P = (T[0] + R * math.cos(math.radians(B)), T[1] + R * math.sin(math.radians(B)))
    if P[1] > -14 or P[1] < -140 or P[0] > 735 or P[0] < 515: continue
    e.load(base)
    go_to(e, P[0], P[1], maxf=300, tol=3)
    p = player(e)
    if p['action'] != 33 or math.hypot(p['x'] - P[0], p['z'] - P[1]) > 6: continue
    toward = math.degrees(math.atan2(T[1] - p['z'], T[0] - p['x'])) % 360
    s = st(toward, 80); n += 1
    e.step(D_CBUTTON, *s, 2)
    arrived = False; landed = False
    for K in range(1, 60):
        q = player(e)
        if not arrived and math.hypot(q['x'] - T[0], q['z'] - T[1]) < 4: arrived = True
        b = 0
        if spin and not landed and K > 4 and q['action'] in (0, 1, 2): landed = True; b = Z
        e.step(b, *((0, 0) if arrived else s), 2); q = player(e)
        if q['action'] in (0, 1, 2) and 540 <= q['x'] <= 584 and -30 <= q['z'] <= -8:
            ok, sp = try_clip()
            if ok:
                hits += 1
                rec = {'T': T, 'R': R, 'B': B, 'spin': spin, 'P': [round(P[0], 1), round(P[1], 1)], 'stick': s, 'K': K,
                       'arrived': arrived, 'at': [round(q['x'], 2), round(q['z'], 2)], 'speed': sp}
                fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec, flush=True)
    if n % 20 == 0: print('tried', n, 'hits', hits, flush=True)
print('done', hits)
