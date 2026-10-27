"""pra_18 RTA setup search (random): from the ALIGNED corner (see pra18_setup2.py), play 1-3 random held segments
(angle, magnitude, frames, optional neutral stop), and on every frame of the last segment try C-down (also after
a 1-frame neutral stop). Each clip found from start 0 is then replayed from all 6 aligned starts.
DIAGNOSTIC SETUP as pra18_setup3.py. usage: pra18_setup_rand.py MODE SEED EPISODES OUT.jsonl"""
import os, sys, json, math, random
from emu import *
from pm import *
from nav import go_to
mode, seed, EP, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rng = random.Random(seed)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sr%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
if mode == 'ns':
    STARTS = [(510, -60), (515, -90), (530, -75), (520, -120), (545, -50), (560, -100)]
    ALIGN = [(90, 30), (20, 30), (270, 40), (90, 30), (20, 30)]   # pin Mario, then up 40 + re-pin pins Laki too
    crossed = lambda q: q['z'] > 0
else:
    STARTS = [(640, 60), (660, 30), (630, 100), (680, 50), (650, 80), (700, 40)]
    ALIGN = [(270, 30), (200, 30), (90, 40), (270, 30), (200, 30)]  # pin Mario, then down 40 + re-pin pins Laki too
    crossed = lambda q: q['z'] < 0
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2); b0 = '/dev/shm/pmbot/sr%d_b.st' % os.getpid(); e.save(b0)
aligned = []
for si, (sx, sz) in enumerate(STARTS):
    e.load(b0)
    if mode == 'sn':                                                                                  # DIAGNOSTIC
        for n in npcs(e):
            if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
    fx, fz = sx + 60, sz + (-60 if mode == 'ns' else 60)
    e.wf32(PLAYER + PS_POS, float(fx)); e.wf32(PLAYER + PS_POS + 8, float(fz))                         # DIAGNOSTIC
    L = laki(); e.wf32(L['addr'] + 0x38, fx + 30.0); e.wf32(L['addr'] + 0x40, float(fz))              # DIAGNOSTIC
    for i in range(30): e.step(0, 0, 0, 2)
    go_to(e, sx, sz, maxf=200, tol=3)
    for ang, fr in ALIGN:
        for i in range(fr): e.step(0, *st(ang, 80), 2)
    for i in range(10): e.step(0, 0, 0, 2)
    fn = '/dev/shm/pmbot/sr%d_a%d.st' % (os.getpid(), si); e.save(fn); aligned.append(fn)
cur = '/dev/shm/pmbot/sr%d_cur.st' % os.getpid()
def try_cd(stop):
    e.save(cur)
    for i in range(stop): e.step(0, 0, 0, 2)
    p = player(e); sp = e.f32(laki()['addr'] + 0x18)
    e.step(D_CBUTTON, 0, 0, 2)
    for i in range(30): e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and crossed(q)
    e.load(cur)
    return ok, (round(p['x'], 2), round(p['z'], 2), round(sp, 2))
def play(fn, segs, upto, stop):
    e.load(fn)
    for k, (a, m, n) in enumerate(segs):
        nn = n if k < len(segs) - 1 else upto
        for i in range(nn): e.step(0, *st(a, m), 2)
    return try_cd(stop)
fo = open(out, 'a'); found = 0
for ep in range(EP):
    segs = [(rng.choice(range(0, 360, 15)), rng.choice((30, 55, 80)), rng.randint(1, 30)) for _ in range(rng.randint(1, 3))]
    e.load(aligned[0])
    for a, m, n in segs[:-1]:
        for i in range(n): e.step(0, *st(a, m), 2)
    a, m, n = segs[-1]
    for f in range(1, n + 1):
        e.step(0, *st(a, m), 2)
        for stop in (0, 1):
            ok, info = try_cd(stop)
            if ok:
                cand = [s for s in segs]
                okall = [int(play(fn, cand, f, stop)[0]) for fn in aligned]
                rec = {'ep': ep, 'segs': cand, 'last_frames': f, 'stop': stop, 'at': info, 'ok': okall}
                fo.write(json.dumps(rec) + '\n'); fo.flush(); found += 1
                print('CLIP', sum(okall), '/6', rec, flush=True)
                e.load(aligned[0])
                for aa, mm, nn in segs[:-1]:
                    for i in range(nn): e.step(0, *st(aa, mm), 2)
                for i in range(f): e.step(0, *st(a, m), 2)
    if ep % 50 == 0: print('ep', ep, 'found', found, flush=True)
print('done', found)
