"""replay states/pra01_corner_seq.json from states/pra01_top_rock.st; print where Lakilester ends (determinism check)"""
import json, math, os
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rpc')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
e.load('states/pra01_top_rock.st'); e.step(0, 0, 0, 2)
for item in json.load(open('states/pra01_corner_seq.json')):
    g, th, sl = item if len(item) == 3 else (*item, 2)
    p, l = player(e), laki()
    deg = math.degrees(math.atan2(l['z'] - p['z'], l['x'] - p['x'])) + th
    sx, sy = stick_for(deg % 360, 80)
    for i in range(g): e.step(0, sx, sy, 2)
    for i in range(sl): e.step(0, 0, 0, 2)
p, l = player(e), laki(); print('mario %.1f %.1f laki %.1f %.1f' % (p['x'], p['z'], l['x'], l['z']))
