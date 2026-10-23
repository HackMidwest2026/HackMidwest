"""Inputs only. From an out-of-bounds STATE, hold one raw stick direction (and optionally jump) for N frames and log
Laki every frame. Flags frames where Laki jumps > 15 units (teleport) and runs where he stays within 4 units of Mario.
usage: isk11_oob_scan.py STATE OUT.jsonl  env N ANGS"""
import json, math, os, sys
from emu import *
from pm import *
STATE = 0x8010D188
N = int(os.environ.get('N', '300'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/osc%d' % os.getpid())
lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
fo = open(sys.argv[2], 'a')
for ang in [float(a) for a in os.environ.get('ANGS', '0,45,90,135,180,225,270,315').split(',')]:
    for mode in ('walk', 'jump'):
        e.load(sys.argv[1]); sx, sy = int(round(80 * math.cos(math.radians(ang)))), int(round(80 * math.sin(math.radians(ang))))
        log = []; prev = lk()
        for f in range(N):
            b = A if (mode == 'jump' and f % 30 < 10) else 0
            e.step(b, sx, sy, 2); p, l = player(e), lk()
            jump = math.hypot(l['x'] - prev['x'], l['z'] - prev['z']); prev = l
            log.append([f, round(p['x'], 1), round(p['y'], 1), round(p['z'], 1), round(l['x'], 1), round(l['y'], 1), round(l['z'], 1), round(l['speed'], 2), e.u32(STATE) >> 16, round(jump, 1), p['action'], where(e)[1]])
            if where(e)[1] != 10: break
        tele = [r for r in log if r[9] > 15]
        inside = sum(1 for r in log if math.hypot(r[1] - r[4], r[3] - r[6]) < 4)
        rec = {'ang': ang, 'mode': mode, 'tele': tele[:20], 'n_tele': len(tele), 'inside_frames': inside, 'minMy': min(r[2] for r in log), 'maxspd': max(r[7] for r in log), 'log': log}
        fo.write(json.dumps(rec) + '\n'); fo.flush()
        print(ang, mode, 'teleports', len(tele), 'inside', inside, 'Mario min y', rec['minMy'], 'Laki max speed', rec['maxspd'], 'end M', log[-1][1:4], 'L', log[-1][4:7], flush=True)
