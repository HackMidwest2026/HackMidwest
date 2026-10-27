"""pra_18 south->north with only pure UP (from below) or pure LEFT (from the right) plus a spin for speed.
Dismount holding the direction, spin (Z) s frames after landing, optionally cancel the spin with the hammer (B) after
c spin frames, keep holding the direction; C-down tried on every grounded, non-spinning frame 20..70 after the dismount.
DIAGNOSTIC SETUP: Mario mounts at a fixed spot, then Lakilester (with Mario riding) is placed at the dismount spot so the
dismount x/z is exact; Laki's speed is never written. usage: pra18_sn_cardspin.py MODE PART NPARTS OUT.jsonl"""
import os, sys, json, math, itertools
from emu import *
from pm import *
mode, part, nparts, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cs%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, 650.0); e.wf32(PLAYER + PS_POS + 8, 110.0)                     # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
b0 = '/dev/shm/pmbot/cs%d_b.st' % os.getpid(); e.save(b0)
cur = '/dev/shm/pmbot/cs%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for i in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and q['z'] < 0; e.load(cur); return ok, sp
if mode == 'up':
    stick = (0, 80)
    spots = [(612.0 + 0.25 * i, z) for i in range(18) for z in range(110, 141, 6)]
else:
    stick = (-80, 0)
    spots = [(x, z) for x in range(700, 741, 8) for z in range(16, 45, 2)]
jobs = list(itertools.product(spots, (0, 2, 4, 6), (None, 4, 6, 8, 10, 12)))[part::nparts]
fo = open(out, 'a'); hits = 0; n = 0; topspeed = 0
for (x, z), s, c in jobs:
    e.load(b0); L = laki()
    e.wf32(L['addr'] + 0x38, x); e.wf32(L['addr'] + 0x40, z + 2.0)                     # DIAGNOSTIC dismount spot
    e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
    p0 = player(e); n += 1
    e.step(D_CBUTTON, *stick, 2)
    land = None; spin_k = None; ks = []
    for K in range(1, 71):
        q = player(e); b = 0
        if land is None and K > 4 and q['action'] in (0, 1, 2): land = K
        if land is not None and spin_k is None and K == land + s: b = Z; spin_k = K
        elif spin_k is not None and c is not None and K == spin_k + c: b = B
        e.step(b, *stick, 2); q = player(e)
        if K >= 20 and q['action'] in (0, 1, 2) and q['z'] > 13.5:
            ok, sp = try_clip()
            if sp: topspeed = max(topspeed, sp)
            if ok: ks.append((K, round(sp, 1), round(q['x'], 2), round(q['z'], 1)))
    if ks:
        hits += 1
        rec = {'mode': mode, 'dismount': [round(p0['x'], 2), round(p0['z'], 2)], 'spin_after_landing': s, 'hammer_cancel_after': c, 'clips': ks}
        fo.write(json.dumps(rec) + '\n'); fo.flush(); print('CLIP', rec, flush=True)
    if n % 100 == 0: print('tried', n, 'hits', hits, 'top mount speed %.2f' % topspeed, flush=True)
print('done', hits, 'top mount speed %.2f' % topspeed)
