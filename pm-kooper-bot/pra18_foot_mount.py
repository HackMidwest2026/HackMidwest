"""Does a plain C-down mount from standing clip through the mirror? DIAGNOSTIC: Mario is placed on foot at each spot,
Lakilester placed APPROACH units away (direction given), 40 idle steps to settle, then C-down; success = riding on the other side."""
import os, sys, json, math
from emu import *
from pm import *
side = sys.argv[1]
e = Emu('pm-jp.z64', '/dev/shm/pmbot/fm%d' % os.getpid())
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
e.load('states/pra18_e2.st'); e.step(0, 0, 0, 2)
base = '/dev/shm/pmbot/fm%d_base.st' % os.getpid(); e.save(base)
if side == 'S': xs, zs, cross = range(604, 624), range(14, 44, 2), (lambda q: q['z'] < 0)
else: xs, zs, cross = range(560, 640, 2), range(-44, -10, 2), (lambda q: q['z'] > 0)
res = []
for x in xs:
    for z in zs:
        for ang in range(0, 360, 45):
            e.load(base)
            e.wf32(PLAYER + PS_POS, float(x)); e.wf32(PLAYER + PS_POS + 8, float(z))                       # DIAGNOSTIC
            L = laki(); a = math.radians(ang)
            e.wf32(L['addr'] + 0x38, x + 30 * math.cos(a)); e.wf32(L['addr'] + 0x40, z + 30 * math.sin(a))   # DIAGNOSTIC
            for i in range(40): e.step(0, 0, 0, 2)
            p = player(e)
            if abs(p['x'] - x) > 1 or abs(p['z'] - z) > 1: continue
            e.step(D_CBUTTON, 0, 0, 2)
            for i in range(40): e.step(0, 0, 0, 2)
            q = player(e)
            if q['action'] == 33 and cross(q): res.append([x, z, ang, round(q['x'], 1), round(q['z'], 1)])
    print(x, len(res), flush=True)
json.dump(res, open('/tmp/claude-0/pm/p18/foot_%s.json' % side, 'w'))
print('done', len(res))
