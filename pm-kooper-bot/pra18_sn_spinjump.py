"""pra_18 south->north, user's speed method: dismount far from the clip line, spin on landing, jump out of the spin
(keeps the spin's ~8-9 units/frame in the air) toward the line, optionally reverse in the air, land, C-down on a
grounded frame. Lakilester starts following ~32 frames after the dismount press with speed ~0.25*distance (capped at 6
while Mario is above him), so Mario should land on the line right then. Grid: dismount distance R and bearing B from
target T, jump frame J into the spin, A held h frames, reverse frame r. C-down tried on every grounded frame 20..55.
DIAGNOSTIC SETUP as pra18_sn_wait.py. usage: pra18_sn_spinjump.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
from nav import go_to
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sj%d' % os.getpid())
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
base = '/dev/shm/pmbot/sj%d_b.st' % os.getpid(); e.save(base)
cur = '/dev/shm/pmbot/sj%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for i in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and q['z'] < 0; e.load(cur); return ok, sp
T = (615.0, 30.0)
jobs = list(itertools.product(range(100, 221, 20), range(0, 181, 15), range(1, 16, 2), (1, 4, 8), (None, 2, 5, 9)))[part::nparts]
fo = open(out, 'a'); hits = 0; best = 0; n = 0; topspeed = 0
for R, B, J, h, r in jobs:
    P = (T[0] + R * math.cos(math.radians(B)), T[1] + R * math.sin(math.radians(B)))
    if P[1] < 14 or P[1] > 140 or P[0] > 737 or P[0] < 513: continue
    e.load(base); go_to(e, P[0], P[1], maxf=300, tol=3)
    p = player(e)
    if p['action'] != 33: continue
    toward = math.degrees(math.atan2(T[1] - p['z'], T[0] - p['x'])) % 360
    s = st(toward, 80); n += 1
    e.step(D_CBUTTON, *s, 2)
    phase = 'hop'; land_k = None; jump_k = None
    for K in range(1, 56):
        q = player(e); b = 0; hold = s
        if phase == 'hop' and K > 4 and q['action'] in (0, 1, 2): phase = 'spin'; b = Z; land_k = K
        elif phase == 'spin' and K == land_k + J: phase = 'air'; b = A; jump_k = K
        elif phase == 'air':
            if K - jump_k < h: b = A
            if r is not None and K - jump_k >= r: hold = (-s[0], -s[1])
            if q['action'] in (0, 1, 2) and K - jump_k > 3: phase = 'ground'
        if phase == 'ground': hold = (0, 0)
        e.step(b, *hold, 2); q = player(e)
        if K >= 20 and phase == 'ground' and q['action'] in (0, 1, 2) and 611.5 <= q['x'] <= 616.3 and 14 <= q['z'] <= 46:
            ok, sp = try_clip()
            if sp is None: continue
            topspeed = max(topspeed, sp)
            if ok:
                hits += 1
                rec = {'R': R, 'B': B, 'J': J, 'h': h, 'r': r, 'P': [round(P[0], 1), round(P[1], 1)], 'stick': s, 'K': K,
                       'at': [round(q['x'], 2), round(q['z'], 2)], 'speed': round(sp, 2)}
                fo.write(json.dumps(rec) + '\n'); fo.flush()
                if sp > best: best = sp
                print('CLIP', rec, flush=True)
    if n % 50 == 0: print('tried', n, 'hits', hits, 'best clip speed %.2f' % best, 'top speed on line %.2f' % topspeed, flush=True)
print('done', hits, best)
