"""Exploration: which Laki spots on/near the lock ledge give an intact flight west to the frozen target.
Ring state RING; Laki placed (RAM) at (lx, ly, lz), Mario placed next to him on the ledge, settle; Mario then walks
south (toward (lx-10, lz+150)). Logs min Laki x, whether follow state 15 (catch-up, target lost) appeared, max speed.
usage: isk11_ledge_scan.py RING OUT.jsonl"""
import json, math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
e = Emu('pm-jp.z64', '/dev/shm/pmbot/ils%d' % os.getpid())
fo = open(sys.argv[2], 'a')
XR = [int(v) for v in os.environ.get('XR', '286,410,8').split(',')]; ZR = [int(v) for v in os.environ.get('ZR', '392,472,8').split(',')]
for lx in range(*XR):
    for lz in range(*ZR):
        e.load(sys.argv[1]); a = [q for q in npcs(e) if q['id'] == -4][0]['addr']
        e.wf32(PLAYER + PS_POS, lx + 6); e.wf32(PLAYER + PS_POS + 4, -440); e.wf32(PLAYER + PS_POS + 8, lz + 18)
        e.wf32(a + 0x38, lx); e.wf32(a + 0x3C, -455); e.wf32(a + 0x40, lz)
        for i in range(25): e.step(0, 0, 0, 2)
        q = player(e); L = [q for q in npcs(e) if q['id'] == -4][0]
        if (e.u32(STATE) >> 16) != 5 or math.hypot(L['x'] - lx, L['z'] - lz) > 4: continue
        T = (lx - 10, lz + 150); seen = set(); minx = 1e9; mx = 0
        for f in range(70):
            q = player(e); st = stick_for(math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x'])) % 360, 80)
            e.step(0, st[0], st[1], 2)
            L = [q for q in npcs(e) if q['id'] == -4][0]; s = e.u32(STATE) >> 16; seen.add(s)
            minx = min(minx, L['x']); mx = max(mx, L['speed'])
        rec = {'laki': [lx, round(L['y'], 1), lz], 'mario_y': round(q['y'], 1), 'states': sorted(seen), 'minx': round(minx, 1), 'maxspd': round(mx, 1)}
        fo.write(json.dumps(rec) + '\n'); fo.flush()
