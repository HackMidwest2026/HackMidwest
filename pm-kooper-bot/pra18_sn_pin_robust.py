"""pra_18 south->north stick-pin setup robustness: dismount at P + (dx, dz) holding V, keep holding V, C-down on
frames 28..40; also nearby stick vectors. DIAGNOSTIC SETUP as pra18_sn_wait.py."""
import os, sys, json, math
from emu import *
from pm import *
from nav import go_to
e = Emu('pm-jp.z64', '/dev/shm/pmbot/pr%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
e.wf32(PLAYER + PS_POS, 650.0); e.wf32(PLAYER + PS_POS + 8, 45.0)                      # DIAGNOSTIC
L = laki(); e.wf32(L['addr'] + 0x38, 630.0); e.wf32(L['addr'] + 0x40, 45.0)           # DIAGNOSTIC
for i in range(30): e.step(0, 0, 0, 2)
e.step(D_CBUTTON, 0, 0, 2)
for i in range(40): e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/pr%d_b.st' % os.getpid(); e.save(base)
cur = '/dev/shm/pmbot/pr%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for i in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and q['z'] < 0; e.load(cur); return ok, sp
P0 = (644.6, 108.7)
tot = ok_n = 0
for V in [(-22, 56), (-21, 53), (-23, 59), (-22, 55), (-22, 57)]:
    for dx in (-3, -2, -1, 0, 1, 2, 3):
        for dz in (-3, -2, -1, 0, 1, 2, 3):
            e.load(base); go_to(e, P0[0] + dx, P0[1] + dz, maxf=300, tol=0.6)
            e.step(D_CBUTTON, *V, 2); ks = []
            for K in range(1, 41):
                e.step(0, *V, 2); q = player(e)
                if K >= 28 and q['action'] in (0, 1, 2):
                    ok, sp = try_clip()
                    if ok: ks.append((K, round(sp, 1)))
            tot += 1; ok_n += bool(ks)
            if ks: print('V', V, 'shift', (dx, dz), 'clip K', ks, flush=True)
print('clipping setups', ok_n, '/', tot)
