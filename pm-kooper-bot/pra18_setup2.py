"""pra_18 RTA setup search v2 for the mirror clips. Setup =
  (1) ALIGN: two held directions that pin Mario in the same corner from any start
      ns: down 30f, then right-slightly-down (20 deg) 30f  -> (574.7, -13.3) mirror / pillar west face
      sn: up 30f, then left-slightly-up (200 deg) 30f      -> (625.3, 13.3) pillar south-east corner
  (2) NORMALIZE: walk a fixed path away from the corner along the mirror (L frames, angle AWAY) and back (angle BACK),
      so Lakilester, who follows Mario's movement history, ends in the same place whatever the start was
  (3) ns: keep holding BACK and press C-down on frame R of the return walk
      sn: after R return frames, hold a1 (down-left) n1 frames, then C-down
Success = riding on the other side 30 frames later; each setup is scored over 6 start spots.
DIAGNOSTIC SETUP: Mario placed 85 units from each start and walked there with real input so Lakilester trails
naturally; in sn Clubba 3 is parked out of the room (stands in for 'already defeated'). Everything else is real input.
usage: pra18_setup2.py MODE PART NPARTS OUT.json"""
import os, sys, json, math, itertools
from emu import *
from pm import *
from nav import go_to
mode, part, nparts, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/s2%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
if mode == 'ns':
    STARTS = [(510, -60), (515, -90), (530, -75), (520, -120), (545, -50), (560, -100)]
    ALIGN = [(90, 30), (20, 30)]
    AWAY, BACK = 165, 15            # left along the mirror (slightly down keeps him on it), then back right
    crossed = lambda q: q['z'] > 0
else:
    STARTS = [(640, 60), (660, 30), (630, 100), (680, 50), (650, 80), (700, 40)]
    ALIGN = [(270, 30), (200, 30)]
    AWAY, BACK = 345, 195           # right along the mirror (slightly up), then back left
    crossed = lambda q: q['z'] < 0
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2); b0 = '/dev/shm/pmbot/s2%d_b.st' % os.getpid(); e.save(b0)
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
    p = player(e); print('start', si, 'aligned (%.2f, %.2f)' % (p['x'], p['z']), flush=True)
    fn = '/dev/shm/pmbot/s2%d_a%d.st' % (os.getpid(), si); e.save(fn); aligned.append(fn)
Ls = [15, 25, 35, 50]
MAGS = [40, 80]
res = []
jobs = list(itertools.product(Ls, MAGS))[part::nparts]
for Lf, mag in jobs:
    # per start: walk away L frames, then return; at each return frame R try the finish
    table = {}
    for si, fn in enumerate(aligned):
        e.load(fn)
        for i in range(Lf): e.step(0, *st(AWAY, mag), 2)
        for R in range(0, 46):
            if R > 0: e.step(0, *st(BACK, mag), 2)
            cur = '/dev/shm/pmbot/s2%d_cur.st' % os.getpid(); e.save(cur)
            if mode == 'ns':
                finishes = [('cd', None, 0)]
            else:
                finishes = [('a1', a1, n1) for a1 in (100, 120, 135, 150, 165, 180) for n1 in (0, 1, 2, 3, 4, 6, 8)]
            for kind, a1, n1 in finishes:
                e.load(cur)
                for i in range(n1): e.step(0, *st(a1, mag), 2)
                e.step(D_CBUTTON, *(st(BACK, mag) if mode == 'ns' else (0, 0)), 2)
                for i in range(30): e.step(0, 0, 0, 2)
                q = player(e)
                table.setdefault((R, a1, n1), []).append(int(q['action'] == 33 and crossed(q)))
            e.load(cur)
    for (R, a1, n1), ok in table.items():
        res.append([Lf, mag, R, a1, n1, ok])
        if sum(ok) >= 3: print('HIT %d/6' % sum(ok), 'L', Lf, 'mag', mag, 'R', R, 'a1', a1, 'n1', n1, ok, flush=True)
    print('done L', Lf, 'mag', mag, flush=True)
json.dump(res, open(out, 'w')); print('done')
