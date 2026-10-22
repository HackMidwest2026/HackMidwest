"""Exploration: from the ring state, put Laki at (x, y, z) on/over the lock ledge and Mario 25 units east of him (RAM),
then Mario walks to the bottom-floor spot T. Logs whether Laki's dash toward the frozen target survives (no hop state)
and how far west he gets, then his speed history as he returns.  usage: isk11_dash_scan.py RING OUT.jsonl"""
import json, math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
T = (367.0, 545.0)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ids%d' % os.getpid())
fo = open(sys.argv[2], 'a')
for lx in range(290, 375, 10):
    for lz in range(395, 470, 10):
        for ly in (-450, -430):
            e.load(sys.argv[1]); a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
            mx, mz = lx + 22, lz + 10
            e.wf32(PLAYER + PS_POS, mx); e.wf32(PLAYER + PS_POS + 4, -468); e.wf32(PLAYER + PS_POS + 8, mz)
            e.wf32(a + 0x38, lx); e.wf32(a + 0x3C, ly); e.wf32(a + 0x40, lz)
            for i in range(10): e.step(0, 0, 0, 2)
            q = player(e)
            if abs(q['y'] + 470) > 2 or (e.u32(STATE) >> 16) != 5: continue
            l0 = [q for q in npcs(e) if q['id'] == -4][0]
            log = []; arrived = None
            for f in range(160):
                q = player(e)
                dd = math.hypot(T[0] - q['x'], T[1] - q['z'])
                if dd > 3: st = stick_for(math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x'])) % 360, 80 if dd > 12 else 25)
                else: st = (0, 0)
                e.step(0, st[0], st[1], 2)
                L = [q for q in npcs(e) if q['id'] == -4][0]; q = player(e)
                log.append((f, e.u32(STATE) >> 16, round(L['x'], 1), round(L['y'], 1), round(L['z'], 1), round(L['speed'], 2), round(math.hypot(L['x'] - q['x'], L['z'] - q['z']), 1)))
            states = [r[1] for r in log]
            minx = min(r[2] for r in log)
            rec = {'laki0': [round(l0['x'], 1), round(l0['y'], 1), round(l0['z'], 1)], 'hop': any(s in (1, 2, 3) for s in states), 'minx': minx,
                   'maxspd': max(r[5] for r in log), 'log': log}
            fo.write(json.dumps(rec) + '\n'); fo.flush()
            print(rec['laki0'], 'hop', rec['hop'], 'minx', minx, 'maxspd', rec['maxspd'], flush=True)
