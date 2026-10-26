"""tik_23: Parakarry lift next to the Super Hammer block, jump off (A) after T frames and keep A held for H frames,
stick held toward the block (west). Does Mario land on the block top (y 30)? Inputs only after
states/tik23_westzone_para.st. usage: tik23_para_block2.py OUT.json"""
import os, sys, json
from emu import *
from pm import *
from nav import go_to
CD = 0x0400
e = Emu('pm-jp.z64', '/dev/shm/pmbot/pq%d' % os.getpid())
res = []
for X0 in (-200, -230):
    for T in range(40, 100, 2):
        for H in (2, 30):
            e.load('states/tik23_westzone_para.st'); e.step(0, 0, 0, 2)
            go_to(e, X0, -20, maxf=200, tol=1.5)
            for i in range(4): e.step(0, -60, 0, 1)
            for i in range(10): e.step(0, 0, 0, 2)
            e.step(CD, 0, 0, 2)
            for f in range(T): e.step(0, -80, 0, 1)
            y0 = player(e)['y']; mx = -99; onb = False
            for f in range(H): e.step(A, -80, 0, 1); mx = max(mx, player(e)['y'])
            for f in range(60):
                e.step(0, -80, 0, 1); p = player(e); mx = max(mx, p['y'])
                if p['y'] > 25 and p['action'] in (0, 1, 2): onb = True
            p = player(e)
            r = {'X0': X0, 'T': T, 'H': H, 'y_at_A': round(y0, 1), 'apex': round(mx, 1), 'end': [round(p['x'], 1), round(p['y'], 1), round(p['z'], 1)], 'on_block': onb}
            res.append(r); print(r, flush=True)
json.dump(res, open(sys.argv[1], 'w'))
