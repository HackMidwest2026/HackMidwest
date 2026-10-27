"""pra_18 south->north 'stick pin' setup: dismount at P while holding stick vector V (up and slightly left), keep holding
V the whole time (Mario walks into the pillar's south face and comes to rest on the clip line, x ~615.4-615.7, z ~24.5),
press C-down on frame K after the dismount press. Grid over P and V; reports every clipping K for each (P, V).
DIAGNOSTIC SETUP as pra18_sn_wait.py. usage: pra18_sn_pinsetup.py PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
from nav import go_to
part, nparts, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/pn%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, 650.0); e.wf32(PLAYER + PS_POS + 8, 45.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 630.0); e.wf32(L['addr'] + 0x40, 45.0)           # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/pn%d_b.st' % os.getpid(); e.save(base)
cur = '/dev/shm/pmbot/pn%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for i in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and q['z'] < 0; e.load(cur); return ok, sp
VS = [(-26, 75), (-23, 65), (-24, 68), (-21, 59), (-19, 54), (-25, 72), (-22, 62)]
PS = [(x, z) for x in range(540, 661, 10) for z in range(50, 141, 10)]
jobs = list(itertools.product(PS, VS))[part::nparts]
fo = open(out, 'a'); found = 0
for P, V in jobs:
    e.load(base); go_to(e, P[0], P[1], maxf=300, tol=2)
    p = player(e)
    if p['action'] != 33: continue
    e.step(D_CBUTTON, *V, 2)
    ks = []; rest = None
    for K in range(1, 61):
        e.step(0, *V, 2); q = player(e)
        if 610 <= q['x'] <= 617 and 14 <= q['z'] <= 46 and q['action'] in (0, 1, 2):
            if rest is None: rest = (K, round(q['x'], 2), round(q['z'], 2))
            if K >= 20:
                ok, sp = try_clip()
                if ok: ks.append((K, round(sp, 1), round(q['x'], 2)))
    if ks:
        found += 1
        rec = {'P': [round(p['x'], 1), round(p['z'], 1)], 'V': V, 'arrive': rest, 'clip_K': ks}
        fo.write(json.dumps(rec) + '\n'); fo.flush(); print('SETUP', rec, flush=True)
print('done', found)
