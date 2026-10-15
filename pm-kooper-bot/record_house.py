"""render the blue house clip (mac_02) as png frames with the real video plugin on Xvfb.

inputs: Go-Explore approach to the wall-face landing (house_explore top.json, frames 0-46), jump off the wall face
(stick 305 deg at strength 20, A for 6 frames, then hold up), then from the hover hold up-slightly-right (276 deg)."""
import json, os, subprocess, sys
from emu import Emu
from pm import *
from corner_sweep import stick_for
from house_explore import BASES
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
A_, Z_ = 0x80, 0x20
V = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/house_wallface_approach.json')))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/vidh')
e.load('states/mac02_start.st')
e.step(0, 0, 0, 2)
x0, z0 = BASES[V['bi']]
e.wf32(PLAYER + PS_POS, x0); e.wf32(PLAYER + PS_POS + 4, 20.0); e.wf32(PLAYER + PS_POS + 8, z0)
for i in range(6): e.step(0, 0, 0, 2)
for i in range(90): e.step(0, 0, 0, 2)      # let the camera settle; Mario stands still
seq = [(0, 0, 0, 'stand')] * 10
f = 0
for b, deg, mag, n in V['seq']:
    sx, sy = stick_for(deg, mag) if deg is not None else (0, 0)
    for i in range(n):
        if f > 46: break
        seq.append(({'tap': A_ if i == 0 else 0, 'spin': Z_ if i == 0 else 0, 'hold': A_}.get(b, 0), sx, sy, 'approach'))
        f += 1
for i in range(8):
    st = stick_for(305, 20) if i < 6 else stick_for(270, 80)
    seq.append((A_ if i < 6 else 0, st[0], st[1], 'jump off the wall face'))
for i in range(12):
    st = stick_for(270, 80)
    seq.append((0, st[0], st[1], 'hover'))
for i in range(50):
    st = stick_for(276, 80) if i < 20 else (0, 0)
    seq.append((0, st[0], st[1], 'hold up-right'))
log = []
for i, (b, x, y, tag) in enumerate(seq):
    e.step(b, x, y, 2)
    p = player(e)
    log.append({'i': i, 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'action': p['action'], 'floor': e.s16(COLLISION + 2)})
    subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % i)], check=True)
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print('end', log[-1])
