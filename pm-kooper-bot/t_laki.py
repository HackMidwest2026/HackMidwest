"""pra_01 experiments: inputs as a list of (buttons, sx, sy, frames); prints Mario and Lakilester every frame."""
import json, sys
from emu import Emu
from pm import *
CD = 0x0400
e = Emu('pm-jp.z64', '/dev/shm/pmbot/laki')
e.load('states/pra01_start.st')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
f = 0
for b, sx, sy, n in json.loads(sys.argv[1]):
    for i in range(n):
        e.step(b if i == 0 else 0, sx, sy, 2)
        p, l = player(e), laki()
        print(f, 'btn' if (b and i == 0) else '   ', 'mario %7.1f %6.1f %6.1f act %2d' % (p['x'], p['y'], p['z'], p['action']),
              'laki %7.1f %6.1f %6.1f spd %6.2f' % (l['x'], l['y'], l['z'], l['speed']) if l else '', 'mode', e.s16(GAME_MODE))
        f += 1
