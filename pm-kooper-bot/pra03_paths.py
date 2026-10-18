"""pra_03: per-frame Mario positions during a forced-speed C-down mount from one start, for several speeds (for the
figure). usage: pra03_paths.py OUT.json"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/p3path')
w = '/dev/shm/pmbot/p3path'
e.load('states/pra03_e1.st'); e.step(0, 0, 0, 2); e.save(w + '/b.st')
out = {}
for S in (60, 150, 300, 2000):
    e.load(w + '/b.st')
    e.wf32(PLAYER + PS_POS, 100.0); e.wf32(PLAYER + PS_POS + 4, 0.0); e.wf32(PLAYER + PS_POS + 8, -75.0)
    for i in range(12): e.step(0, 0, 0, 2)
    pts = [[player(e)['x'], player(e)['z']]]
    e.step(CD, 0, 0, 2)
    for i in range(25):
        for n in npcs(e):
            if n['id'] == -4 and player(e)['action'] != 33: e.wf32(n['addr'] + 0x18, float(S))
        e.step(0, 0, 0, 2); p = player(e); pts.append([p['x'], p['z']])
    out[S] = pts
json.dump(out, open(sys.argv[1], 'w'))
print({S: (round(v[-1][0], 1), round(v[-1][1], 1)) for S, v in out.items()})
