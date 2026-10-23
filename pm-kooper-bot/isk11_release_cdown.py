"""Inputs only. From STATE, release like isk11_release_test.py (walk direction ANG until 45+ from Laki, then toward
S=(368,520)), press C-down on frame F, then hold toward the isk_19 exit floor. One line per (ang, F): speed the mount
reads, where Mario pressed, isk19 or not.  usage: isk11_release_cdown.py STATE OUT.jsonl  env ANGLES F0 F1"""
import json, math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
ANG = [float(a) for a in os.environ.get('ANGLES', '60,75,90,105,120,135,150').split(',')]
F0, F1 = int(os.environ.get('F0', '5')), int(os.environ.get('F1', '18'))
S = tuple(float(v) for v in os.environ.get('S', '368,520').split(','))
PRE = tuple(float(v) for v in os.environ['PRE'].split(',')) if os.environ.get('PRE') else None
WAIT = int(os.environ.get('WAIT', '0'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/irc%d' % os.getpid())
laki = lambda: [q for q in npcs(e) if q['id'] == -4][0]
fo = open(sys.argv[2], 'a')
def walk(ang, F):
    e.load(sys.argv[1]); phase = 0; h = []; hold = 0; w0 = 0
    for f in range(F + 1):
        q = player(e); L = laki()
        if PRE:
            if phase == 0 and math.hypot(PRE[0] - q['x'], PRE[1] - q['z']) < 2: phase = 1; w0 = f
            tx, tz = PRE if phase == 0 else (q['x'], q['z']) if f - w0 < WAIT else S
        else:
            if phase == 0 and math.hypot(L['x'] - q['x'], L['z'] - q['z']) > 45: phase = 1
            tx, tz = (q['x'] + 100 * math.cos(math.radians(ang)), q['z'] + 100 * math.sin(math.radians(ang))) if phase == 0 else S
        dd = math.hypot(tx - q['x'], tz - q['z'])
        stk = stick_for(math.degrees(math.atan2(tz - q['z'], tx - q['x'])) % 360, (80 if dd > 12 else 25) if (phase or not PRE) else (80 if dd > 8 else 20)) if dd > (1 if PRE and phase == 0 else 2) else (0, 0)
        b = 0
        if hold: hold -= 1; b = A
        elif dd > 2 and len(h) > 3 and q['action'] in (1, 2) and math.hypot(h[-3][0] - q['x'], h[-3][1] - q['z']) < 1: hold = 9; b = A
        if f == F: b |= D_CBUTTON
        e.step(b, stk[0], stk[1], 2); q = player(e); h.append((q['x'], q['z']))
for ang in ANG:
    for F in range(F0, F1 + 1):
        walk(ang, F); pc = player(e); a = laki()['addr']; spd = None
        for i in range(20):
            if e.u8(PLAYER + PS_ACTION) == 33: spd = e.f32(a + 0x18); break
            e.step(0, 0, 0, 2)
        ok = False
        for i in range(160):
            q = player(e); st = stick_for(math.degrees(math.atan2(532 - q['z'], 220 - q['x'])) % 360, 80)
            e.step(0, st[0], st[1], 2)
            if where(e)[1] == 16: ok = True; break
        r = {'ang': ang, 'F': F, 'press': [round(pc['x'], 1), round(pc['y'], 1), round(pc['z'], 1)], 'act': pc['action'],
             'speed': None if spd is None else round(spd, 1), 'isk19': ok}
        fo.write(json.dumps(r) + '\n'); fo.flush(); print(r, flush=True)
