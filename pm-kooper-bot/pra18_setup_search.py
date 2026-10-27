"""pra_18 RTA setup search for the mirror clips. A setup = (1) hold ALIGN angle a0 for 40 frames (pins Mario against
walls so the start no longer matters), (2) neutral w0 frames (Laki settles), (3) hold a1 at mag m1 for n1 frames,
(4) release r frames, (5) C-down. Success = riding on the other side 30 frames later.
Each setup is scored over several start spots. DIAGNOSTIC SETUP: Mario placed 90 units away from each start spot and
walked there with real inputs first, so Lakilester trails naturally; everything after that placement is real input.
usage: pra18_setup_search.py MODE PART NPARTS OUT.json   (MODE ns: north->south, sn: south->north)"""
import os, sys, json, math, itertools
from emu import *
from pm import *
from nav import go_to
mode, part, nparts, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ss%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
# stick deg: 0 right(+x), 90 down(+z, south), 180 left, 270 up(north)
if mode == 'ns':
    STARTS = [(510, -60), (515, -90), (530, -75), (520, -120), (545, -50), (560, -100)]   # just east of statue 2
    ALIGN = [((90, 30), (0, 30)), ((60, 40), (0, 20)), ((90, 30), (20, 30))]   # down into mirror, then right into pillar
    A1 = [120, 150, 180, 210, 240, 270, 300]
    crossed = lambda q: q['z'] > 0
else:
    STARTS = [(640, 60), (660, 30), (630, 100), (680, 50), (600, 120), (650, 80)]   # around Clubba 3's battle spot
    ALIGN = [((270, 30), (180, 30)), ((300, 40), (180, 20)), ((270, 30), (200, 30))]   # up into mirror, then left into pillar
    A1 = [0, 30, 60, 90, 300, 330, 270]
    crossed = lambda q: q['z'] < 0
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2); b0 = '/dev/shm/pmbot/ss%d_b.st' % os.getpid(); e.save(b0)
aligned = {}
for si, (sx, sz) in enumerate(STARTS):
    for a0 in ALIGN:
        for w0 in (0, 15, 40):
            e.load(b0)
            if mode == 'sn':                                                                          # DIAGNOSTIC: Clubba 3
                for n in npcs(e):                                                                     # already defeated ->
                    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)  # park it
            fx, fz = sx + 60, sz + (-60 if mode == 'ns' else 60)
            e.wf32(PLAYER + PS_POS, float(fx)); e.wf32(PLAYER + PS_POS + 8, float(fz))                 # DIAGNOSTIC
            L = laki(); e.wf32(L['addr'] + 0x38, fx + 30.0); e.wf32(L['addr'] + 0x40, float(fz))      # DIAGNOSTIC
            for i in range(30): e.step(0, 0, 0, 2)
            go_to(e, sx, sz, maxf=200, tol=3)
            for (ang, fr) in a0:
                for i in range(fr): e.step(0, *st(ang, 80), 2)
            for i in range(w0): e.step(0, 0, 0, 2)
            fn = '/dev/shm/pmbot/ss%d_%d_%d_%d.st' % (os.getpid(), si, ALIGN.index(a0), w0); e.save(fn)
            p = player(e); aligned[(si, a0, w0)] = fn
            if w0 == 0: print('start', si, 'align', ALIGN.index(a0), '-> mario (%.2f, %.2f)' % (p['x'], p['z']), flush=True)
combos = list(itertools.product(ALIGN, (0, 15, 40), A1, (40, 80), range(1, 31, 3), (0, 1)))[part::nparts]
res = []
for a0, w0, a1, m1, n1, r in combos:
    ok = []
    for si in range(len(STARTS)):
        e.load(aligned[(si, a0, w0)])
        for i in range(n1): e.step(0, *st(a1, m1), 2)
        for i in range(r): e.step(0, 0, 0, 2)
        p = player(e); L = laki(); gap = math.hypot(e.f32(L['addr'] + 0x38) - p['x'], e.f32(L['addr'] + 0x40) - p['z'])
        e.step(D_CBUTTON, 0, 0, 2); s = e.f32(laki()['addr'] + 0x18)
        for i in range(30): e.step(0, 0, 0, 2)
        q = player(e); ok.append(int(q['action'] == 33 and crossed(q)))
    if sum(ok): print('HIT', sum(ok), '/', len(ok), (ALIGN.index(a0), w0, a1, m1, n1, r), ok, flush=True)
    res.append([ALIGN.index(a0), w0, a1, m1, n1, r, ok])
json.dump(res, open(out, 'w')); print('done')
