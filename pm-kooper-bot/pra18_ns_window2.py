"""pra_18 north->south: exact clip window near the pillar's west side. DIAGNOSTIC (map only): Mario placed on foot at
(x, z), Lakilester's speed forced to S each frame until the mount. usage: pra18_ns_window.py X0 X1 OUT.json"""
import os, sys, json
from emu import *
from pm import *
x0, x1, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/nw%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
b0 = '/dev/shm/pmbot/nw%d.st' % os.getpid(); e.save(b0)
res = {}
x = x0
while x <= x1 + 1e-6:
    for z in (-13.0,):
        ok = []
        for k in range(91):
            S = float(os.environ.get("S0", 43)) + 0.1 * k
            e.load(b0)
            e.wf32(PLAYER + PS_POS, x); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, z)
            for i in range(20): e.step(0, 0, 0, 2)
            e.step(D_CBUTTON, 0, 0, 2)
            for i in range(30):
                if player(e)['action'] != 33: e.wf32(laki()['addr'] + 0x18, float(S))
                e.step(0, 0, 0, 2)
            p = player(e)
            if p['action'] == 33 and p['z'] > 0: ok.append(round(S, 1))
        res['%.2f,%.0f' % (x, z)] = ok
        print('%.2f %.0f' % (x, z), (min(ok), max(ok), len(ok)) if ok else None, flush=True)
    x += 0.5
json.dump(res, open(out, 'w')); print('done')
