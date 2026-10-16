"""pra_01 reflected side: arc push, Mario aims at Lakilester plus an offset (ox, oz) each stop-and-go cycle; the
offset can change by phase: 'ox,oz,until' items, until = 'z<-150' / 'x>680' style condition on Lakilester.
usage: rev_arc3.py G S 'ox,oz,cond;...' [save_path]"""
import math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/arc3')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
G, S = int(sys.argv[1]), int(sys.argv[2])
phases = []
for item in sys.argv[3].split(';'):
    ox, oz, cond = item.split(',')
    phases.append((float(ox), float(oz), cond))
def done(cond, l):
    if cond == 'end': return False
    k, op, v = cond[0], cond[1], float(cond[2:])
    val = l['x'] if k == 'x' else l['z']
    return val < v if op == '<' else val > v
e.load(os.environ.get('ST', 'states/pra01_top_rock.st'))
pi, c, f, stuck, last = 0, 0, 0, 0, None
while c < 500 and pi < len(phases):
    p, l = player(e), laki()
    ox, oz, cond = phases[pi]
    if done(cond, l):
        print('phase', pi, 'done at', c, 'laki %.1f %.1f' % (l['x'], l['z'])); pi += 1; continue
    deg = math.degrees(math.atan2(l['z'] + oz - p['z'], l['x'] + ox - p['x']))
    sx, sy = stick_for(deg, 80)
    for i in range(G): e.step(0, sx, sy, 2)
    for i in range(S): e.step(0, 0, 0, 2)
    c += 1; f += G + S
    p, l = player(e), laki()
    if c % 10 == 0: print(c, f, 'ph', pi, 'mario %.1f %.1f laki %.1f %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['z'], l['speed']), flush=True)
    if l['speed'] > 0.01:
        print('LOST at', c, 'mario %.1f %.1f laki %.1f %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['z'], l['speed'])); break
    if last and abs(l['x'] - last[0]) + abs(l['z'] - last[1]) < 0.01:
        stuck += 1
        if stuck > 15: print('STUCK'); break
    else: stuck = 0
    last = (l['x'], l['z'])
p, l = player(e), laki()
print('end', c, f, 'ph', pi, 'mario %.1f %.1f laki %.1f %.1f spd %.1f' % (p['x'], p['z'], l['x'], l['z'], l['speed']))
if len(sys.argv) > 4: e.save(sys.argv[4])
