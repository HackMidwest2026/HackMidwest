"""pra_18 south->north with only pure UP (from directly below) or pure LEFT (from the right) after the dismount.
Feasibility test: Mario placed on foot at the dismount spot (DIAGNOSTIC), mounts (resets Laki's follow history), waits,
dismounts holding the cardinal direction, keeps holding it, and C-down is tried on every frame 26..42 after the
dismount press. Reports which spots/frames clip and the real Laki speed. usage: pra18_sn_cardinal.py MODE OUT.json"""
import os, sys, json
from emu import *
from pm import *
mode, out = sys.argv[1], sys.argv[2]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/cd%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):                                                                      # DIAGNOSTIC
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
b0 = '/dev/shm/pmbot/cd%d_b.st' % os.getpid(); e.save(b0)
cur = '/dev/shm/pmbot/cd%d_c.st' % os.getpid()
def try_clip():
    e.save(cur); e.step(D_CBUTTON, 0, 0, 2); sp = None
    for i in range(30):
        if sp is None and player(e)['action'] == 33: sp = e.f32(laki()['addr'] + 0x18)
        e.step(0, 0, 0, 2)
    q = player(e); ok = q['action'] == 33 and q['z'] < 0; e.load(cur); return ok, sp
if mode == 'up':
    stick = (0, 80); spots = [(614.5 + 0.1 * i, z) for i in range(18) for z in (100, 110, 120, 130)]
else:
    stick = (-80, 0); spots = [(x, z) for x in range(680, 731, 5) for z in (18, 22, 26, 30, 34, 38, 42)]
res = []
for (x, z) in spots:
    e.load(b0)
    e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 8, float(z))                 # DIAGNOSTIC
    L = laki(); e.wf32(L['addr'] + 0x38, x + 20.0); e.wf32(L['addr'] + 0x40, float(z))      # DIAGNOSTIC
    for i in range(30): e.step(0, 0, 0, 2)
    e.step(D_CBUTTON, 0, 0, 2)
    for i in range(40): e.step(0, 0, 0, 2)
    p0 = player(e)
    if p0['action'] != 33: continue
    e.step(D_CBUTTON, *stick, 2)
    ks = []
    for K in range(1, 43):
        e.step(0, *stick, 2); q = player(e)
        if K >= 26 and q['action'] in (0, 1, 2):
            ok, sp = try_clip()
            if ok: ks.append((K, round(sp, 1), round(q['x'], 2), round(q['z'], 1)))
    r = {'spot': [round(p0['x'], 2), round(p0['z'], 2)], 'clips': ks}
    res.append(r)
    if ks: print('CLIP', r, flush=True)
json.dump(res, open(out, 'w')); print('done', sum(1 for r in res if r['clips']), '/', len(res))
