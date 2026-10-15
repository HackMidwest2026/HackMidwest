"""render the human-style Blue House Skip setup (house_setup_tol.py) on Xvfb.

Walk up into the house front at x = -406, spin holding up-right (world 340), jump on spin frame 9 holding
down-left (150) and let go after 10 frames; on the wall face jump again holding (deg2, mag2) for 6 frames, then
hold up-slightly-right (276)."""
import json, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
import house_probe as H, house_setup_tol as T
from corner_sweep import stick_for
from pm import *
OUT, deg2, mag2 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
os.makedirs(OUT, exist_ok=True)
H.init()
e = H.W['e']
e.load(T.stand_at_front(-406))
for i in range(60): e.step(0, 0, 0, 2)
seq = [(0, 0, 0, 'stand against the house front, a few units left of the corner')] * 12
sa = stick_for(340, 80)
seq += [(0x20 if f == 0 else 0, sa[0], sa[1], 'spin up-right past the corner') for f in range(9)]
sl = stick_for(150, 80)
seq += [(0x80 if f < 12 else 0, *(sl if f < 10 else (0, 0)), 'jump, hold down-left, let go before landing') for f in range(14)]
land_at = None
log = []
for i, (b, x, y, tag) in enumerate(seq):
    e.step(b, x, y, 2)
    p = player(e)
    log.append({'i': i, 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'action': p['action'], 'floor': e.s16(COLLISION + 2)})
    subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % i)], check=True)
    if tag.startswith('jump') and p['action'] not in (3, 4, 5, 8) and i > 25:
        break
n = len(log)
s2 = stick_for(deg2, mag2); s3 = stick_for(276, 80)
for f in range(70):
    tag = 'landed on the wall face: jump, light up-right' if f < 6 else ('hold up, slightly right' if f < 40 else 'inside the house')
    st = s2 if f < 6 else (s3 if f < 40 else (0, 0))
    e.step(0x80 if f < 12 else 0, st[0], st[1], 2)
    p = player(e)
    log.append({'i': n + f, 'tag': tag, 'x': p['x'], 'y': p['y'], 'z': p['z'], 'action': p['action'], 'floor': e.s16(COLLISION + 2)})
    subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % (n + f))], check=True)
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print('end', log[-1])
