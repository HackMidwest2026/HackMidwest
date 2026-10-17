"""replay the rev_aim_explore cell with Lakilester furthest into the top-right corner, save it as
states/pra01_corner.st, then run down at several angles: log Lakilester's peak speed, and try C-down on every frame
0..60 of the run (hit = Mario riding on the real side, z > 1).
usage: rev_corner_release.py <arch.json>"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
CD = 0x0400
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/crel')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
arch = json.load(open(sys.argv[1]))
best = max((a for k, a in arch.items() if k != 'seed'), key=lambda a: a.get('d', a['lx'] - a['lz']))
seq = best['seq']
e.load(os.environ.get('SEED', 'states/pra01_top_rock.st')); e.step(0, 0, 0, 2)
for item in seq:
    g, th, sl = item if len(item) == 3 else (*item, 2)
    p, l = player(e), laki()
    deg = math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th
    sx, sy = stick_for(deg % 360, 80)
    for i in range(g): e.step(0, sx, sy, 2)
    for i in range(sl): e.step(0, 0, 0, 2)
p, l = player(e), laki()
print('corner after %d cycles: mario %.1f %.1f laki %.1f %.1f spd %.1f' % (len(seq), p['x'], p['z'], l['x'], l['z'], l['speed']))
e.save(os.environ.get('CORNER', 'states/pra01_corner.st'))
json.dump(seq, open(os.environ.get('CORNER', 'states/pra01_corner.st').replace('.st', '_seq.json'), 'w'))
if os.environ.get('NOREL'): sys.exit(0)
for deg in (90, 80, 100, 110, 120, 135):
    sx, sy = stick_for(deg, 80)
    e.load(os.environ.get('CORNER', 'states/pra01_corner.st')); e.step(0, 0, 0, 2)
    sp = []
    for f in range(60):
        e.step(0, sx, sy, 2)
        p, l = player(e), laki()
        sp.append((round(l['speed'], 1), round(p['x']), round(p['z'])))
    pk = max(range(60), key=lambda i: sp[i][0])
    hits = []
    for f in range(60):
        e.load(os.environ.get('CORNER', 'states/pra01_corner.st')); e.step(0, 0, 0, 2)
        for i in range(f): e.step(0, sx, sy, 2)
        e.step(CD, sx, sy, 2)
        for i in range(28): e.step(0, 0, 0, 2)
        q = player(e)
        if q['action'] == 33 and q['z'] > 1 and tuple(where(e)[:2]) == (21, 0):
            hits.append((f, round(q['x'], 1), round(q['y'], 1), round(q['z'], 1)))
    print('run %d: peak speed %.1f at frame %d (mario %d, %d); speeds %s; hits %s' % (deg, sp[pk][0], pk, sp[pk][1], sp[pk][2], [s[0] for s in sp[:40]], hits), flush=True)
