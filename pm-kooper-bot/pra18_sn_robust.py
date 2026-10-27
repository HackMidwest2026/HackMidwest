"""pra_18 south->north run-and-wait: robustness of found setups. For each hit in sn_wait.jsonl (and its dismount spot
shifted by +-3/+-6 units), report which C-down frames K (after the dismount press) clip and the mount speeds.
DIAGNOSTIC SETUP as pra18_sn_wait.py."""
import os, sys, json, math
from emu import *
from pm import *
from nav import go_to
e = Emu('pm-jp.z64', '/dev/shm/pmbot/sb%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, 650.0); e.wf32(PLAYER + PS_POS + 8, 45.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 630.0); e.wf32(L['addr'] + 0x40, 45.0)           # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/sb%d_b.st' % os.getpid(); e.save(base)
cur = '/dev/shm/pmbot/sb%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for i in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and q['z'] < 0; e.load(cur); return ok, sp
recs = [json.loads(l) for l in open(sys.argv[1])]
for rec in recs:
    T = rec['T']; P0 = rec['P']; s = tuple(rec['stick'])
    print('== setup', rec['P'], 'stick', s, 'orig K', rec['K'], 'speed %.1f' % rec['speed'], flush=True)
    for dx, dz in ((0, 0), (3, 0), (-3, 0), (0, 3), (0, -3), (6, 0), (-6, 0), (0, 6), (0, -6)):
        e.load(base); go_to(e, P0[0] + dx, P0[1] + dz, maxf=300, tol=2)
        e.step(D_CBUTTON, *s, 2); arrived = False; ks = []
        for K in range(1, 50):
            q = player(e)
            if not arrived and math.hypot(q['x'] - T[0], q['z'] - T[1]) < 4: arrived = True
            e.step(0, *((0, 0) if arrived else s), 2); q = player(e)
            if K >= 25 and q['action'] in (0, 1, 2):
                ok, sp = try_clip()
                if ok: ks.append((K, round(sp, 1)))
        print('  shift (%+d,%+d): clipping K %s' % (dx, dz, ks), flush=True)
