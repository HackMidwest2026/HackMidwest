"""Inputs only. For each STATE (Laki idle by Mario, target frozen far left) and each release direction, Mario walks
that way (jumping if blocked) until he is 45+ from Laki, then heads to S=(368,520) and stands. Logs whether Laki kept
the frozen target (never follow state 15), his min x, his peak speed and the frame of the peak.
usage: isk11_release_test.py OUT.jsonl STATE...   env ANGLES (deg, atan2(dz,dx); 90 = south)"""
import json, math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
ANG = [float(a) for a in os.environ.get('ANGLES', '60,75,90,105,120,135,150').split(',')]
S = (368.0, 520.0)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/irt%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
fo = open(sys.argv[1], 'a')
for st in sys.argv[2:]:
    for ang in ANG:
        e.load(st); l0 = laki(); p0 = player(e)
        if (e.u32(STATE) >> 16) != 5: break
        phase = 0; h = []; hold = 0; seen = set(); minx = 1e9; peak = (0, -1); spd = []
        for f in range(130):
            q = player(e); L = laki()
            if phase == 0 and math.hypot(L['x'] - q['x'], L['z'] - q['z']) > 45: phase = 1
            if phase == 0: tx, tz = q['x'] + 100 * math.cos(math.radians(ang)), q['z'] + 100 * math.sin(math.radians(ang))
            else: tx, tz = S
            dd = math.hypot(tx - q['x'], tz - q['z'])
            stk = stick_for(math.degrees(math.atan2(tz - q['z'], tx - q['x'])) % 360, 80 if dd > 12 else 25) if dd > 2 else (0, 0)
            b = 0
            if hold: hold -= 1; b = A
            elif dd > 2 and len(h) > 3 and q['action'] in (1, 2) and math.hypot(h[-3][0] - q['x'], h[-3][1] - q['z']) < 1: hold = 9; b = A
            e.step(b, stk[0], stk[1], 2); q = player(e); h.append((q['x'], q['z'])); L = laki()
            s = e.u32(STATE) >> 16; seen.add(s); minx = min(minx, L['x']); spd.append(round(L['speed'], 1))
            if L['speed'] > peak[0]: peak = (L['speed'], f)
        rec = {'state': os.path.basename(st), 'laki0': [round(l0['x']), round(l0['y']), round(l0['z'])], 'mario0': [round(p0['x']), round(p0['y']), round(p0['z'])],
               'ang': ang, 'lost': 15 in seen, 'states': sorted(seen), 'minx': round(minx, 1), 'peak': round(peak[0], 1), 'peak_f': peak[1],
               'mario_end': [round(q['x']), round(q['y']), round(q['z'])], 'spd': spd}
        fo.write(json.dumps(rec) + '\n'); fo.flush()
