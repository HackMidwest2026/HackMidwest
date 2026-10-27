"""Generic mirror-clip speed map (z = 0 mirror): Mario placed on foot at (x, z) (DIAGNOSTIC), C-down, Lakilester's speed
forced to S each frame until the mount (DIAGNOSTIC, same method as pra18_mount_fine.py). Records which spots/speeds put
Mario riding on the other side. usage: pra_mount_map.py STATE SIDE XLO XHI XSTEP OUT.json   (SIDE n: z<0, s: z>0)"""
import os, sys, json
from emu import *
from pm import *
state, side, xlo, xhi, xs, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/mm%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load(state); e.step(0, 0, 0, 2); b0 = '/dev/shm/pmbot/mm%d.st' % os.getpid(); e.save(b0)
ZS = [int(v) for v in os.environ.get('ZS', '3,8,13,18,25,35').split(',')]
ZS = [-z for z in ZS] if side == 'n' else ZS
SPEEDS = list(range(int(os.environ.get('SLO', '6')), int(os.environ.get('SHI', '100')) + 1, int(os.environ.get('SSTEP', '4')))) + [150, 300]
res = []
for x in range(xlo, xhi + 1, xs):
    for z in ZS:
        for S in SPEEDS:
            e.load(b0)
            e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, float(z))
            for i in range(20): e.step(0, 0, 0, 2)
            p0 = player(e)
            if abs(p0['x'] - x) > 1 or abs(p0['z'] - z) > 1.5 or abs(p0['y']) > 2:
                res.append((x, z, None, 'unstandable')); break
            e.step(D_CBUTTON, 0, 0, 2)
            for i in range(30):
                if player(e)['action'] != 33: e.wf32(laki()['addr'] + 0x18, float(S))
                e.step(0, 0, 0, 2)
            p = player(e)
            if p['action'] == 33 and ((p['z'] > 0) if side == 'n' else (p['z'] < 0)):
                res.append((x, z, S, 'CROSS', round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)))
    print(x, sum(1 for r in res if r[3] == 'CROSS'), flush=True)
json.dump(res, open(out, 'w')); print('done')
