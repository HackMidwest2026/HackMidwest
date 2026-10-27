"""pra_18 north side: how close to the mirror (z = 0) can Mario's centre get while riding / dismounting Lakilester?
Target: z >= -9.8 near x 717-723 (inside Clubba 3's 80-unit trigger). DIAGNOSTIC SETUP: Mario placed at (723,-20) on foot
with Laki; mount with C-down; everything after is real input. Phase 1: hold angle a1 (mag m1) n1 frames; phase 2: hold
a2 (m2) n2 frames; phase 3: neutral 0-2 frames then optional C-down dismount (holding a3). Tracks Mario z every frame.
usage: pra18_laki_z.py PART NPARTS OUT.json"""
import os, sys, json, math, itertools
from emu import *
from pm import *
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/lz%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
dist = lambda p: math.hypot(p['x'] - 717, p['z'] - 70)
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, 723.0); e.wf32(PLAYER + PS_POS + 8, -25.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 703.0); e.wf32(L['addr'] + 0x40, -25.0)           # DIAGNOSTIC
for i in range(40): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
assert player(e)['action'] == 33
b0 = '/dev/shm/pmbot/lz%d_0.st' % os.getpid(); e.save(b0)
def st(deg, mag): return int(round(mag * math.cos(math.radians(deg)))), -int(round(mag * math.sin(math.radians(deg))))
# stick deg: 0 = right (+x), 90 = down (toward mirror, +z), 180 = left
A1 = [60, 75, 90, 105, 120]; A2 = [0, 20, 45, 70, 90, 110, 135, 160, 180, 200, 270, None]
combos = list(itertools.product(A1, (40, 80), (12, 30), A2, (40, 80), (1, 3, 8, 20)))[part::nparts]
best = {'ride': (-99,), 'dismount': (-99,)}; res = []
for a1, m1, n1, a2, m2, n2 in combos:
    e.load(b0)
    for i in range(n1): e.step(0, *st(a1, m1), 2)
    s2 = (0, 0) if a2 is None else st(a2, m2)
    zr = (-99,)
    for i in range(n2):
        e.step(0, *s2, 2); p = player(e)
        if p['z'] > zr[0] and p['z'] < 0: zr = (p['z'], p['x'], dist(p), i)
    if zr[0] > best['ride'][0]: best['ride'] = zr + ((a1, m1, n1, a2, m2, n2),)
    mid = '/dev/shm/pmbot/lz%d_m.st' % os.getpid(); e.save(mid)
    for w, a3 in itertools.product((0, 1, 2), (None, 90, 0, 180)):
        e.load(mid)
        for i in range(w): e.step(0, 0, 0, 2)
        s3 = (0, 0) if a3 is None else st(a3, 80)
        e.step(D_CBUTTON, *s3, 2); zd = (-99,)
        for i in range(35):
            e.step(0, *s3, 2); p = player(e)
            if p['z'] > zd[0] and p['z'] < 0: zd = (p['z'], p['x'], dist(p), i, p['action'])
        if zd[0] > best['dismount'][0]: best['dismount'] = zd + ((a1, m1, n1, a2, m2, n2, w, a3),)
        if zd[0] > -11 or zr[0] > -11: res.append([zr, zd, (a1, m1, n1, a2, m2, n2, w, a3)])
        if zd[2] < 80 if len(zd) > 2 else False: print('HIT dismount', zd, (a1, m1, n1, a2, m2, n2, w, a3), flush=True)
    if len(zr) > 2 and zr[2] < 80: print('HIT ride', zr, flush=True)
print('best', best, flush=True)
json.dump({'best': best, 'close': res}, open(out, 'w'))
