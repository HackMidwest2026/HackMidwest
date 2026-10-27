"""pra_18 south->north, pure LEFT: which dismount spots (x, z) clip, and on which C-down frames?
DIAGNOSTIC: Mario mounts at a fixed spot, then Lakilester (with Mario riding) is placed at the dismount spot so the
dismount x/z is exact; dismount holding full left, keep holding left, C-down on frames 28..40. Laki's speed is never
written. usage: pra18_sn_left_fine.py XLO XHI STEP OUT.json"""
import os, sys, json
from emu import *
from pm import *
xlo, xhi, step, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/lf%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, 680.0); e.wf32(PLAYER + PS_POS + 8, 60.0)                      # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
b0 = '/dev/shm/pmbot/lf%d_b.st' % os.getpid(); e.save(b0)
cur = '/dev/shm/pmbot/lf%d_c.st' % os.getpid()
res = []
n = int(round((xhi - xlo) / step)) + 1
for i in range(n):
    x = xlo + i * step
    for z in (18, 24, 30, 36, 42):
        e.load(b0); L = laki()
        e.wf32(L['addr'] + 0x38, x); e.wf32(L['addr'] + 0x40, z + 2.0)                 # DIAGNOSTIC dismount spot
        e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
        p0 = player(e)
        e.step(D_CBUTTON, -80, 0, 2); ks = []
        for K in range(1, 41):
            e.step(0, -80, 0, 2); q = player(e)
            if K >= 28 and q['action'] in (0, 1, 2):
                e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
                for j in range(30):
                    if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
                    e.step(0, 0, 0, 2)
                r = player(e); e.load(cur)
                if r['action'] == 33 and r['z'] < 0: ks.append((K, round(sp, 2), round(q['x'], 2)))
        res.append([round(p0['x'], 3), round(p0['z'], 2), ks])
        if ks: print('dismount (%.3f, %.2f) clips %s' % (p0['x'], p0['z'], ks), flush=True)
json.dump(res, open(out, 'w')); print('done')
