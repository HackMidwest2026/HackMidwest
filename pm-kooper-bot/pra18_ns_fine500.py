"""pra_18 north->south: fine speed map at the spots near x 500..540 (just north of the mirror, east of statue 2).
DIAGNOSTIC (map only): Mario placed on foot at (x, z), Lakilester's speed forced to S each frame until the mount.
usage: pra18_ns_fine500.py X OUT.json   (z -13..-21, S 30..120 step 0.5)"""
import os, sys, json
from emu import *
from pm import *
x, out = int(sys.argv[1]), sys.argv[2]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/nf%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
b0 = '/dev/shm/pmbot/nf%d.st' % os.getpid(); e.save(b0)
res = {}
for z in (-13, -15, -17, -19, -21):
    ok = []
    for k in range(181):
        S = 30 + 0.5 * k
        e.load(b0)
        e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, float(z))
        for i in range(20): e.step(0, 0, 0, 2)
        p0 = player(e)
        if abs(p0['x'] - x) > 0.6 or abs(p0['z'] - z) > 0.6: ok = None; break
        e.step(D_CBUTTON, 0, 0, 2)
        for i in range(30):
            if player(e)['action'] != 33: e.wf32(laki()['addr'] + 0x18, float(S))
            e.step(0, 0, 0, 2)
        p = player(e)
        if p['action'] == 33 and p['z'] > 0: ok.append(S)
    res[z] = ok
    print(x, z, ok, flush=True)
json.dump(res, open(out, 'w')); print('done')
