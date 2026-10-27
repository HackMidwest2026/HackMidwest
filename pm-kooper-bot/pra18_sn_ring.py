"""pra_18 south->north: leave Lakilester far from the pillar tip and spin to it. Ride to P (ring around the clip spot
T=(614,26) at distance R and bearing B), dismount holding the stick toward T, spin (Z) on landing holding toward T
(optional chained second spin), try C-down on every frame. Success = riding on the north side.
DIAGNOSTIC SETUP: Mario placed on foot at (650,45) (Clubba 3 parked = already defeated), mounts and rides 40 frames
(resets Laki's follow history); riding to P uses go_to (real stick input); everything after is real input.
usage: pra18_sn_ring.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
from nav import go_to
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sg%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
T = (614.0, 26.0)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, 650.0); e.wf32(PLAYER + PS_POS + 8, 45.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 630.0); e.wf32(L['addr'] + 0x40, 45.0)           # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
assert player(e)['action'] == 33
base = '/dev/shm/pmbot/sg%d_b.st' % os.getpid(); e.save(base)
cur = '/dev/shm/pmbot/sg%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for i in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and q['z'] < 0; e.load(cur); return ok, sp
# stick angle convention: 0 = +x, 90 = +z; bearing B from T to P in the same convention
jobs = list(itertools.product(range(60, 201, 20), range(-10, 191, 10), (-6, 0, 6), (None, 4, 8)))[part::nparts]
fo = open(out, 'a'); hits = 0; n = 0
for R, B, off, rev in jobs:
    P = (T[0] + R * math.cos(math.radians(B)), T[1] + R * math.sin(math.radians(B)))
    if P[1] < 14 or P[1] > 140 or P[0] > 735 or P[0] < 515: continue
    e.load(base)
    go_to(e, P[0], P[1], maxf=250, tol=3)
    p = player(e)
    if p['action'] != 33 or math.hypot(p['x'] - P[0], p['z'] - P[1]) > 6: continue
    toward = (math.degrees(math.atan2(T[1] - p['z'], T[0] - p['x'])) + off) % 360
    s = st(toward, 80)
    e.step(D_CBUTTON, *s, 2)
    for i in range(30):
        e.step(0, *s, 2)
        if player(e)['action'] in (0, 1, 2) and i > 3: break
    e.step(Z, *s, 2); n += 1
    spun = '/dev/shm/pmbot/sg%d_s.st' % os.getpid(); e.save(spun)
    for J in range(3, 40, 2):                                   # jump J frames into the spin (cancels it)
        e.load(spun)
        for i in range(J): e.step(0, *s, 2)
        e.step(A, *s, 2)
        for f in range(40):
            hold = s if (rev is None or f < rev) else (-s[0], -s[1])
            e.step(A if f < 6 else 0, *hold, 2); q = player(e)
            if not (598 <= q['x'] <= 632 and 8 <= q['z'] <= 50): continue
            ok, sp = try_clip()
            if ok:
                hits += 1
                rec = {'R': R, 'B': B, 'off': off, 'rev': rev, 'P': [round(P[0], 1), round(P[1], 1)], 'stick': s, 'J': J, 'f': f,
                       'at': [round(q['x'], 2), round(q['z'], 2), round(q['y'], 1), q['action']], 'speed': sp}
                fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec, flush=True)
    if n % 20 == 0: print('tried', n, 'hits', hits, flush=True)
print('done', hits)
