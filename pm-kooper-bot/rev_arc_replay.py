"""replay the furthest-right idle cell from a rev_arc_explore archive, save it, then try more push cycles to the right
with a few stick angles and print what happens. usage: rev_arc_replay.py <arch.json>"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/arr')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
arch = json.load(open(sys.argv[1]))
best = max(arch.values(), key=lambda a: a['lx'] - a['lz'])
seq = best['seq']
print('cycles', len(seq), seq)
e.load('states/pra01_top_rock.st'); e.step(0, 0, 0, 2)
for g, deg in seq:
    sx, sy = stick_for(deg, 80)
    for i in range(g): e.step(0, sx, sy, 2)
    e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
p, l = player(e), laki()
print('at mario %.1f %.1f %.1f laki %.1f %.1f %.1f spd %.1f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], l['speed']))
e.save('states/pra01_arc_top.st')
for deg in (0, 345, 15, 330, 30):
    e.load('states/pra01_arc_top.st'); e.step(0, 0, 0, 2)
    sx, sy = stick_for(deg, 80)
    out = []
    for c in range(12):
        e.step(0, sx, sy, 2); e.step(0, 0, 0, 2); e.step(0, 0, 0, 2)
        p, l = player(e), laki()
        out.append('M(%.0f,%.0f,%.0f) L(%.0f,%.0f,%.0f) %.1f' % (p['x'], p['y'], p['z'], l['x'], l['y'], l['z'], l['speed']))
    print(deg, ' | '.join(out[::2]))
