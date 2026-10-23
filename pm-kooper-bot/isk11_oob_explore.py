"""Inputs only. Replay the 2-frame release from states/ledgeR_w180.st (step to (358,484), walk to (366,498), C-down on
release frame 10), then steer while riding toward STEER instead of the isk_19 exit floor. Optionally dismount (C-down)
DISM frames after landing and walk toward WALK. Logs Mario, Laki, follow state, map every frame.
usage: isk11_oob_explore.py OUT.json  env STEER=x,z DISM WALK=x,z N SAVE"""
import json, math, os, sys
from emu import *
from pm import *
from corner_sweep import stick_for
STATE = 0x8010D188
P = lambda k, d: tuple(float(v) for v in os.environ.get(k, d).split(','))
STEER, WALK = P('STEER', '100,560'), P('WALK', '0,560'); DISM = int(os.environ.get('DISM', '-1')); N = int(os.environ.get('N', '300'))
e = Emu('pm-jp.z64', '/dev/shm/pmbot/oob%d' % os.getpid())
lk = lambda: [q for q in npcs(e) if q['id'] == -4][0]
e.load('states/ledgeR_w180.st')
PRE, S = (358.0, 484.0), (366.0, 498.0); ph = 0; h = []; hold = 0
for f in range(11):
    q = player(e)
    if ph == 0 and math.hypot(PRE[0] - q['x'], PRE[1] - q['z']) < 2: ph = 1
    tx, tz = PRE if ph == 0 else S
    dd = math.hypot(tx - q['x'], tz - q['z'])
    stk = stick_for(math.degrees(math.atan2(tz - q['z'], tx - q['x'])) % 360, (80 if dd > 12 else 25) if ph else (80 if dd > 8 else 20)) if dd > (2 if ph else 1) else (0, 0)
    b = 0
    if hold: hold -= 1; b = A
    elif dd > 2 and len(h) > 3 and q['action'] in (1, 2) and math.hypot(h[-3][0] - q['x'], h[-3][1] - q['z']) < 1: hold = 9; b = A
    if f == 10: b |= D_CBUTTON
    e.step(b, stk[0], stk[1], 2); q = player(e); h.append((q['x'], q['z']))
log = []; landed = 0 if os.environ.get('DISMF') else None
if os.environ.get('DISMF'): DISM = int(os.environ['DISMF'])
for f in range(N):
    q = player(e)
    if landed is None or DISM < 0 or f < landed + DISM: T = STEER
    else: T = WALK
    st = stick_for(math.degrees(math.atan2(T[1] - q['z'], T[0] - q['x'])) % 360, 80) if math.hypot(T[0] - q['x'], T[1] - q['z']) > 3 else (0, 0)
    b = D_CBUTTON if (landed is not None and DISM >= 0 and f == landed + DISM) else 0
    e.step(b, st[0], st[1], 2); q, l = player(e), lk()
    if os.environ.get('DISMF'): pass
    elif landed is None and f > 20 and abs(q['y'] - log[-1]['M'][1]) < 0.01 if log else False: landed = f
    r = {'f': f, 'M': [round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)], 'act': q['action'], 'L': [round(l['x'], 1), round(l['y'], 1), round(l['z'], 1)],
         'ls': round(l['speed'], 2), 'st': e.u32(STATE) >> 16, 'map': where(e)[1], 'dML': round(math.hypot(q['x'] - l['x'], q['z'] - l['z']), 1)}
    log.append(r)
    if r['map'] != 10: break
if os.environ.get('SAVE'): e.save(os.environ['SAVE'])
json.dump({'landed': landed, 'log': log}, open(sys.argv[1], 'w'))
for r in log[::10] + log[-1:]: print(r)
print('landed', landed)
