"""render the low Blue House entry (mac_02): Mario standing in the corner notch at (-395.2, -141.0), hold up slightly
left (raw stick -8, 80). STEP_UP carries him past both wall lines at y ~29 and the push-out puts him inside."""
import json, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H
from pm import *
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
H.init()
e = H.W['e']
e.load(H.base(-395.2, -141.0))
for i in range(60): e.step(0, 0, 0, 2)
p = player(e); print('start', p)
seq = [(0, 0, 0, 'standing in the corner notch')] * 15 + [(0, -8, 80, 'hold up (slightly left)')] * 40
log = []
for i, (b, x, y, tag) in enumerate(seq):
    e.step(b, x, y, 2)
    p = player(e)
    if tag.startswith('hold') and p['action'] == 34: tag = 'STEP_UP: 3-unit move with no wall test'
    if H.inside(p): tag = 'inside the house (y %.0f)' % p['y']
    log.append({'i': i, 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'action': p['action']})
    subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % i)], check=True)
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print('end', log[-1])
