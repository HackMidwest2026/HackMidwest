"""pra_18 south->north: maximise Lakilester's mount speed at the follow onset while Mario stands on the clip line
(x 612..616.2, z 14..46; the clip needs speed >= ~21 at x 616, 34 at 614, 48 at 612). Episode: ride to a random spot,
dismount holding D1, run D1 n1 frames, then hold D2 (often the reverse) n2 frames, then release; try C-down on every
grounded frame 20..50 after the dismount press while Mario is on the line. Logs speed and clip result.
DIAGNOSTIC SETUP as pra18_sn_wait.py. usage: pra18_sn_spike.py SEED EPISODES OUT.jsonl"""
import os, sys, json, math, random
from emu import *
from pm import *
from nav import go_to
seed, EP, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rng = random.Random(seed)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sk%d' % os.getpid())
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
base = '/dev/shm/pmbot/sk%d_b.st' % os.getpid(); e.save(base)
cur = '/dev/shm/pmbot/sk%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for i in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and q['z'] < 0; e.load(cur); return ok, sp
fo = open(out, 'a'); best = 0; hits = 0
for ep in range(EP):
    P = (rng.uniform(520, 735), rng.uniform(20, 140))
    e.load(base); go_to(e, P[0], P[1], maxf=250, tol=4)
    p = player(e)
    if p['action'] != 33: continue
    D1 = rng.choice(range(0, 360, 10)); n1 = rng.randint(0, 25)
    D2 = rng.choice([(D1 + 180) % 360] * 3 + list(range(0, 360, 10))); n2 = rng.randint(1, 30)
    m1 = rng.choice((55, 80)); m2 = rng.choice((30, 55, 80))
    seq = []
    e.step(D_CBUTTON, *st(D1, m1), 2); seq.append((D_CBUTTON, D1, m1))
    for K in range(1, 51):
        if K <= n1: s, a, m = st(D1, m1), D1, m1
        elif K <= n1 + n2: s, a, m = st(D2, m2), D2, m2
        else: s, a, m = (0, 0), 0, 0
        e.step(0, *s, 2); seq.append((0, a, m)); q = player(e)
        if K >= 20 and q['action'] in (0, 1, 2) and 611.5 <= q['x'] <= 616.3 and 14 <= q['z'] <= 46:
            ok, sp = try_clip()
            if sp is None: continue
            if ok: hits += 1
            if ok or sp > 30:
                rec = {'P': [round(P[0], 1), round(P[1], 1)], 'seq': seq[:], 'K': K, 'at': [round(q['x'], 2), round(q['z'], 2)], 'speed': round(sp, 2), 'ok': ok}
                fo.write(json.dumps(rec) + '\n'); fo.flush()
            if ok and sp > best:
                best = sp; print('CLIP speed %.2f at (%.2f, %.2f) K %d P %s D1 %d n1 %d D2 %d n2 %d' % (sp, q['x'], q['z'], K, rec['P'], D1, n1, D2, n2), flush=True)
    if ep % 100 == 0: print('ep', ep, 'hits', hits, 'best clip speed %.2f' % best, flush=True)
print('done', hits, best)
