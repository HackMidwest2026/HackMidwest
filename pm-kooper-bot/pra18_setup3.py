"""pra_18 RTA setup search v3 for the mirror clips, built on the 'reversal dash': when Mario reverses direction,
Lakilester (standing still) suddenly dashes along Mario's old path with a large moveSpeed (35-47 seen); pressing C-down
during the dash makes the mount read that speed. Setup =
  (1) ALIGN (pins Mario in the same corner from any start; see pra18_setup2.py)
  (2) hold AWAY angle a for n frames
  (3) hold reverse angle b for m frames (m = 1..12), C-down on the next frame
Success = riding on the other side 30 frames later; scored over 6 start spots.
DIAGNOSTIC SETUP: Mario placed 85 units from each start and walked there with real input so Lakilester trails
naturally; in sn Clubba 3 is parked out of the room (stands in for 'already defeated'). Everything else is real input.
usage: pra18_setup3.py MODE PART NPARTS OUT.json"""
import os, sys, json, math, itertools
from emu import *
from pm import *
from nav import go_to
mode, part, nparts, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/s3%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
st = lambda deg, mag: (int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg)))))
if mode == 'ns':
    STARTS = [(510, -60), (515, -90), (530, -75), (520, -120), (545, -50), (560, -100)]
    ALIGN = [(90, 30), (20, 30)]
    AWAY = [180, 200, 225, 250, 270]          # left / up-left / up
    REV = [0, 20, 45, 70, 90]                 # back toward the corner
    crossed = lambda q: q['z'] > 0
else:
    STARTS = [(640, 60), (660, 30), (630, 100), (680, 50), (650, 80), (700, 40)]
    ALIGN = [(270, 30), (200, 30)]
    AWAY = [0, 20, 45, 70, 90, 120]           # right / down-right / down / down-left
    REV = [180, 200, 225, 250, 270]           # back toward the pillar tip
    crossed = lambda q: q['z'] < 0
NS_ = list(range(4, 41, 4))
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2); b0 = '/dev/shm/pmbot/s3%d_b.st' % os.getpid(); e.save(b0)
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
    fn = '/dev/shm/pmbot/s3%d_a%d.st' % (os.getpid(), si); e.save(fn); aligned.append(fn)
jobs = list(itertools.product(AWAY, NS_, (40, 80)))[part::nparts]
cur = '/dev/shm/pmbot/s3%d_cur.st' % os.getpid()
res = []
for a, n, mag in jobs:
    table = {}
    for si, fn in enumerate(aligned):
        for b in REV:
            e.load(fn)
            for i in range(n): e.step(0, *st(a, mag), 2)
            for m in range(1, 13):
                e.step(0, *st(b, 80), 2); e.save(cur)
                sp = e.f32(laki()['addr'] + 0x18)
                e.step(D_CBUTTON, 0, 0, 2)
                for i in range(30): e.step(0, 0, 0, 2)
                q = player(e); ok = int(q['action'] == 33 and crossed(q))
                table.setdefault((b, m), []).append((ok, round(sp, 1)))
                e.load(cur)
    for (b, m), v in table.items():
        ok = [x[0] for x in v]
        res.append([a, n, mag, b, m, ok, [x[1] for x in v]])
        if sum(ok) >= 2: print('HIT %d/6' % sum(ok), 'away', a, 'n', n, 'mag', mag, 'rev', b, 'm', m, ok, 'speeds', [x[1] for x in v], flush=True)
    print('done', a, n, mag, flush=True)
json.dump(res, open(out, 'w')); print('done')
