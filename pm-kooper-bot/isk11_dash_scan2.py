"""Exploration: ring state; Laki at (lx, LY, lz) near the lock ledge, Mario on the -600 floor at (mx, mz) within the
tether (RAM). Settle 20 frames (Laki must stay in state 5), then Mario walks to T. Log Laki per frame.
usage: isk11_dash_scan2.py RING OUT.jsonl  env T=x,z LY"""
import json, math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
T = tuple(float(v) for v in os.environ.get('T', '367,545').split(','))
LY = float(os.environ.get('LY', '-450'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ids2%d' % os.getpid())
fo = open(sys.argv[2], 'a')
for lx in range(300, 411, 10):
    for lz in range(385, 446, 10):
        for (dx, dz) in ((0, 30), (20, 25), (-20, 30), (30, 10)):
            mx, mz = lx + dx, lz + dz
            e.load(sys.argv[1]); a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
            e.wf32(PLAYER + PS_POS, mx); e.wf32(PLAYER + PS_POS + 4, -598); e.wf32(PLAYER + PS_POS + 8, mz)
            e.wf32(a + 0x38, lx); e.wf32(a + 0x3C, LY); e.wf32(a + 0x40, lz)
            for i in range(20): e.step(0, 0, 0, 2)
            q = player(e); L = [q for q in npcs(e) if q['id'] == -4][0]
            if abs(q['y'] + 600) > 2 or (e.u32(STATE) >> 16) != 5 or abs(L['x'] - lx) > 3: continue
            l0 = (round(L['x'], 1), round(L['y'], 1), round(L['z'], 1)); m0 = (round(q['x'], 1), round(q['z'], 1))
            log = []
            for f in range(110):
                q = player(e); dd = math.hypot(T[0] - q['x'], T[1] - q['z'])
                st = stick_for(math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x'])) % 360, 80 if dd > 12 else 25) if dd > 3 else (0, 0)
                e.step(0, st[0], st[1], 2)
                L = [q for q in npcs(e) if q['id'] == -4][0]; q = player(e)
                log.append((f, e.u32(STATE) >> 16, round(L['x'], 1), round(L['y'], 1), round(L['z'], 1), round(L['speed'], 2), round(math.hypot(L['x'] - q['x'], L['z'] - q['z']), 1)))
            st_ = [r[1] for r in log]
            rec = {'laki0': l0, 'mario0': m0, 'hop': any(s in (1, 2, 3) for s in st_), 'minx': min(r[2] for r in log), 'maxspd': max(r[5] for r in log), 'log': log}
            fo.write(json.dumps(rec) + '\n'); fo.flush()
            print(l0, m0, 'hop', rec['hop'], 'minx', rec['minx'], 'maxspd', rec['maxspd'], flush=True)
