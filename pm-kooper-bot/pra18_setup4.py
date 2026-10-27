"""pra_18 RTA setup search v4: copies the structure of the two clips found earlier, starting from the PINNED state
(Mario and Lakilester in the same spot from any start, see pra18_setup_rand.py ALIGN).
  ns: hold a1 k1 frames (walk up-right to a waypoint, Laki trails), wait w (Laki settles), hold a2 (down-left) n frames,
      then flick the stick back (a2+180) m frames (Laki's reversal dash) and press C-down
  sn: hold a1 k1 frames (walk down / down-left to a waypoint), wait w, hold a2 (up) at mag2 n frames toward the pillar tip,
      neutral s frames, C-down
Each hit from start 0 is replayed from all 6 pinned starts. DIAGNOSTIC SETUP as pra18_setup3.py.
usage: pra18_setup4.py MODE PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
from nav import go_to
mode, part, nparts, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/s4%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
if mode == 'ns':
    STARTS = [(510, -60), (515, -90), (530, -75), (520, -120), (545, -50), (560, -100)]
    ALIGN = [(90, 30), (20, 30), (270, 40), (90, 30), (20, 30)]
    crossed = lambda q: q['z'] > 0
    PRE = list(itertools.product((285, 300, 315, 330, 345), range(6, 21, 2), (0, 10, 30), (120, 135, 150, 165), (80,)))
    NMAX, FIN = 24, [('flick', m) for m in (1, 2, 3, 4)]
else:
    STARTS = [(640, 60), (660, 30), (630, 100), (680, 50), (650, 80), (700, 40)]
    ALIGN = [(270, 30), (200, 30), (90, 40), (270, 30), (200, 30)]
    crossed = lambda q: q['z'] < 0
    PRE = list(itertools.product((100, 115, 130, 145, 160), range(2, 17, 2), (0, 10, 30), (255, 265, 275, 285), (40, 55)))
    NMAX, FIN = 16, [('stop', s) for s in (0, 1, 2)]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2); b0 = '/dev/shm/pmbot/s4%d_b.st' % os.getpid(); e.save(b0)
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
    fn = '/dev/shm/pmbot/s4%d_a%d.st' % (os.getpid(), si); e.save(fn); aligned.append(fn)
cur = '/dev/shm/pmbot/s4%d_cur.st' % os.getpid()
def finish(a2, kind, m):
    if kind == 'flick':
        for i in range(m): e.step(0, *st(a2 + 180, 80), 2)
    else:
        for i in range(m): e.step(0, 0, 0, 2)
    p = player(e); sp = e.f32(laki()['addr'] + 0x18)
    e.step(D_CBUTTON, 0, 0, 2)
    for i in range(30): e.step(0, 0, 0, 2)
    q = player(e)
    return q['action'] == 33 and crossed(q), (round(p['x'], 2), round(p['z'], 2), round(sp, 2))
def full(fn, a1, k1, w, a2, mag2, n, kind, m):
    e.load(fn)
    for i in range(k1): e.step(0, *st(a1, 80), 2)
    for i in range(w): e.step(0, 0, 0, 2)
    for i in range(n): e.step(0, *st(a2, mag2), 2)
    return finish(a2, kind, m)[0]
fo = open(out, 'a'); hits = 0
for idx, (a1, k1, w, a2, mag2) in enumerate(PRE[part::nparts]):
    e.load(aligned[0])
    for i in range(k1): e.step(0, *st(a1, 80), 2)
    for i in range(w): e.step(0, 0, 0, 2)
    for n in range(1, NMAX + 1):
        e.step(0, *st(a2, mag2), 2); e.save(cur)
        for kind, m in FIN:
            e.load(cur)
            ok, info = finish(a2, kind, m)
            if ok:
                okall = [int(full(fn, a1, k1, w, a2, mag2, n, kind, m)) for fn in aligned]
                rec = {'a1': a1, 'k1': k1, 'w': w, 'a2': a2, 'mag2': mag2, 'n': n, 'fin': kind, 'm': m, 'at': info, 'ok': okall}
                fo.write(json.dumps(rec) + '\n'); fo.flush(); hits += 1
                print('CLIP %d/6' % sum(okall), rec, flush=True)
        e.load(cur)
    if idx % 20 == 0: print('prefix', idx, '/', len(PRE[part::nparts]), 'hits', hits, flush=True)
print('done', hits)
