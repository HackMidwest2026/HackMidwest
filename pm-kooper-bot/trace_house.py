"""replay one house_explore archive entry and print every frame"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from house_explore import BASES
from corner_sweep import stick_for
from pm import *
A_, Z_ = 0x80, 0x20
v = json.load(open(sys.argv[1]))
H.init()
e = H.W['e']
e.load(H.base(*BASES[v['bi']]))
f = 0
for b, deg, mag, n in v['seq']:
    sx, sy = stick_for(deg, mag) if deg is not None else (0, 0)
    for i in range(n):
        bb = {'tap': A_ if i == 0 else 0, 'spin': Z_ if i == 0 else 0, 'hold': A_}.get(b, 0)
        e.step(bb, sx, sy, 2)
        p = player(e)
        print(f, b, deg, mag, 'x %.2f y %.2f z %.2f' % (p['x'], p['y'], p['z']), 'act', p['action'], 'floor', e.s16(COLLISION + 2), 'yaw %.0f' % e.f32(PLAYER + 0x80))
        f += 1
