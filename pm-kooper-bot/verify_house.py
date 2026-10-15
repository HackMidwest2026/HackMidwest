"""replay one full blue house clip (Go-Explore approach + wall-face jump + hover inputs) and print where Mario ends."""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_wallface as W
from corner_sweep import stick_for
from pm import *
H = W.H
hv = json.loads(sys.argv[1])
W.init()
e = H.W['e']
e.load(H.W['wf'])
for f in range(8):
    e.step(0x80 if f < 6 else 0, *(stick_for(305, 20) if f < 6 else stick_for(270, 80)), 2)
a1, m1, n1, a2, m2, b = hv
for f in range(n1 + 90):
    st = stick_for(a1, m1) if f < n1 else (stick_for(a2, m2) if f < n1 + 15 else (0, 0))
    e.step(0, st[0], st[1], 2)
    p = player(e)
    if f < 30 or f % 10 == 0:
        print(f, 'x %.2f y %.2f z %.2f' % (p['x'], p['y'], p['z']), 'act', p['action'], 'floor', e.s16(COLLISION + 2), 'mode', e.s16(GAME_MODE))
