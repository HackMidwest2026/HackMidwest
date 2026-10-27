"""pra_18 south->north: which mount speeds clip from each standing spot near the east pillar's south tip?
DIAGNOSTIC (map only): Mario placed on foot at (x, z), Lakilester's speed forced to S each frame until the mount
(same method as pra18_mount_fine.py). usage: pra18_sn_minspeed.py XLO XHI OUT.json"""
import os, sys, json
from emu import *
from pm import *
xlo, xhi, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ms%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
for n in npcs(e):
    if n['id'] in (2, 5): e.wf32(n['addr'] + 0x3C, -1000.0); e.wf32(n['addr'] + 0x38, 2000.0)
b0 = '/dev/shm/pmbot/ms%d.st' % os.getpid(); e.save(b0)
res = {}
for x in [xlo + 0.1 * i for i in range(int(round((xhi - xlo) * 10)) + 1)]:
    for z in (20, 30, 40):
        ok = []
        for S in [s * 0.5 for s in range(6, 90)]:
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
            if p['action'] == 33 and p['z'] < 0: ok.append(S)
        res['%.1f,%d' % (x, z)] = ok
        if ok: print('%.1f' % x, z, 'min', min(ok), 'max', max(ok), 'n', len(ok), flush=True)
json.dump(res, open(out, 'w')); print('done')
