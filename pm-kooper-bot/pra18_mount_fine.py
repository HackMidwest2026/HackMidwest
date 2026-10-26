"""pra_18 (Bridge Mirror Hall): Lakilester mount (C-down) with his speed forced to S (DIAGNOSTIC: Mario placed on a
grid, Lakilester's speed written each frame until the mount). Which spots/speeds put Mario on the other side of the
mirror (z = 0)?  usage: pra18_mount_map.py SIDE XLO XHI OUT.json   (SIDE n: start z<0, s: start z>0)"""
import os, sys, json
from emu import *
from pm import *
side, xlo, xhi, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/pm%d' % os.getpid())
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
ZS = [-z for z in range(1, 41, 2)] if side == 'n' else list(range(1, 41, 2))
SPEEDS = tuple(range(int(os.environ.get('SLO','20')), int(os.environ.get('SHI','100')) + 1, 2))
res = []
for x in range(xlo, xhi + 1, 1):
    for z in ZS:
        for S in SPEEDS:
            e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
            e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, float(z))
            for i in range(20): e.step(0, 0, 0, 2)
            p0 = player(e)
            if abs(p0['x'] - x) > 1 or abs(p0['z'] - z) > 1 or (p0['z'] < 0) != (side == 'n'):
                res.append((x, z, S, 'moved', round(p0['x'], 1), round(p0['z'], 1))); break
            e.step(D_CBUTTON, 0, 0, 2)
            for i in range(30):
                if player(e)['action'] != 33:
                    l = laki()
                    if l: e.wf32(l['addr'] + 0x18, float(S))
                e.step(0, 0, 0, 2)
            p = player(e)
            crossed = (p['z'] > 0) if side == 'n' else (p['z'] < 0)
            if crossed and p['action'] == 33:
                res.append((x, z, S, 'CROSS', round(p['x'], 1), round(p['z'], 1)))
                print('CROSS', x, z, S, '->', round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), flush=True)
json.dump(res, open(out, 'w'))
print('done', len([r for r in res if r[3] == 'CROSS']), 'crossings')
