"""pra_02 mirror clip experiments: inputs as JSON list of [buttons, sx, sy, frames]; logs Mario and Lakilester."""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/pra02t')
e.load(sys.argv[2] if len(sys.argv) > 2 else 'states/pra02_start.st')


def laki():
    for n in npcs(e):
        if n['id'] == -4: return n


f = 0
quiet = os.environ.get('QUIET')
for b, sx, sy, n in json.loads(sys.argv[1]):
    for i in range(n):
        e.step(b if i == 0 else 0, sx, sy, 2)
        p, l = player(e), laki()
        if not quiet or i == n - 1:
            print(f, '%5s' % hex(b) if (b and i == 0) else '     ', '(%3d,%3d)' % (sx, sy),
                  'mario %7.2f %6.1f %7.2f act %2d' % (p['x'], p['y'], p['z'], p['action']),
                  'laki %7.2f %6.1f %7.2f spd %6.2f yaw %5.1f' % (l['x'], l['y'], l['z'], l['speed'], e.f32(l['addr'] + 0x34)) if l else '',
                  'map', where(e)[:2])
        f += 1
if os.environ.get('SAVE'):
    e.save(os.environ['SAVE'])
