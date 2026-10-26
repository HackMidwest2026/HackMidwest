"""tik_23: try to land on top of the Super Hammer block (top y 30, east face x -255) with Parakarry: stand at X facing
west, C-down (lift), press A T frames later (jump off = start_bounce_b) while holding left. Logs apex and where
Mario lands. usage: tik23_para_block.py   (inputs only after the setup state states/tik23_westzone_para.st)"""
import os, json
from emu import *
from pm import *
from nav import go_to
CD = 0x0400
e = Emu('pm-jp.z64', '/dev/shm/pmbot/pb%d' % os.getpid())
res = []
for X in (-262, -270, -275, -280):
    for T in range(0, 60, 3):
        e.load('states/tik23_westzone_para.st'); e.step(0, 0, 0, 2)
        go_to(e, X + 20, -20, maxf=200, tol=1.5)
        for i in range(4): e.step(0, -60, 0, 1)          # face west, up against the block if close
        for i in range(10): e.step(0, 0, 0, 2)
        x0 = player(e)['x']
        e.step(CD, 0, 0, 2)
        mx = -99
        for f in range(T): e.step(0, 0, 0, 1); mx = max(mx, player(e)['y'])
        e.step(A, -80, 0, 2)
        for f in range(80): e.step(0, -80, 0, 1); mx = max(mx, player(e)['y'])
        p = player(e)
        r = {'X': X, 'x0': round(x0, 1), 'T': T, 'apex': round(mx, 1), 'end': [round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)], 'action': p['action']}
        res.append(r); print(r, flush=True)
json.dump(res, open('/tmp/claude-0/pm/tik23_para_block.json', 'w'))
