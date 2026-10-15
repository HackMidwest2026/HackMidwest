"""render the reproduced jan_04 log clip (rice plugin on Xvfb) and log mario's state each game frame."""
import os, subprocess, sys, json
from emu import *
from pm import *
OUT = sys.argv[1]
SHIFT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0      # optional start-z nudge for a failing comparison run
os.makedirs(OUT, exist_ok=True)
e = Emu('pm-jp.z64', '/dev/shm/pmbot/vidjan')
e.load('states/jan04_start.st')
e.step(0, 0, 0, 2)
e.w8(game_status(e) + 0x74, 1)
e.wf32(PLAYER + PS_POS, -137.0); e.wf32(PLAYER + PS_POS + 4, 2.457098); e.wf32(PLAYER + PS_POS + 8, 37.07176 + SHIFT)
for i in range(100):
    e.step(0, 0, 0, 2)
seq = [(0, 0, 0, 'stand')] * 8 + [(Z, -128, 26, 'spin')] + [(Z, -128, 26, 'spin')] * 4 + \
      [(A | Z, -128, 26, 'jump')] * 11 + [(A, -128, -100, 'switch')] * 12
log = []
for i, (b, x, y, tag) in enumerate(seq):
    e.step(b, x, y, 2)
    p = player(e)
    log.append({'i': i, 'tag': tag, 'stick': (x, y), 'x': p['x'], 'y': p['y'], 'z': p['z'], 'action': p['action'],
                'yaw': e.f32(PLAYER + PS_TARGETYAW)})
    subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'g%04d.png' % i)], check=True)
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print('end', [round(log[-1][k], 2) for k in ('x', 'y', 'z')])
