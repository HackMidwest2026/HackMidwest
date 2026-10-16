"""pra_01 driver: inputs as JSON list of [buttons, sx, sy, frames]; logs Mario and Lakilester (last frame of each
segment if QUIET). Optional second arg: start state. SAVE=path saves the end state."""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/pra01t')
e.load(sys.argv[2] if len(sys.argv) > 2 else 'states/pra01_start.st')


def laki():
    for n in npcs(e):
        if n['id'] == -4: return n


f = 0
for b, sx, sy, n in json.loads(sys.argv[1]):
    for i in range(n):
        e.step(b if i == 0 else 0, sx, sy, 2)
        p, l = player(e), laki()
        if not os.environ.get('QUIET') or i == n - 1:
            print(f, '(%3d,%3d)' % (sx, sy), 'mario %7.2f %6.1f %7.2f act %2d' % (p['x'], p['y'], p['z'], p['action']),
                  'laki %7.2f %6.1f %7.2f spd %6.2f yaw %5.1f' % (l['x'], l['y'], l['z'], l['speed'], e.f32(l['addr'] + 0x34)) if l else '', 'map', where(e)[:2])
        f += 1
if os.environ.get('SAVE'):
    e.save(os.environ['SAVE'])
