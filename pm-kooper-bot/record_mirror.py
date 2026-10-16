"""render the pra_02 mirror clip on Xvfb: stop-and-go push from the left pillar until Mario x >= 712, down 10,
right 4, walk up slowly (0, 20) and C-down on frame 1 of the walk-up."""
import json, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
CD = 0x0400
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rmir')
e.load('states/pra02_leftpillar.st')
for i in range(30): e.step(0, 0, 0, 2)
seq = [(0, 0, 0, 'Mario at the left pillar, Lakilester on his right facing left')] * 10
# the push, generated against the real position
log, i = [], 0


def laki():
    for n in npcs(e):
        if n['id'] == -4: return n


def step(b, sx, sy, tag):
    global i
    e.step(b, sx, sy, 2)
    p, l = player(e), laki()
    log.append({'i': i, 'tag': tag, 'x': p['x'], 'z': p['z'], 'y': p['y'], 'lx': l['x'], 'lz': l['z'], 'ls': l['speed'], 'act': p['action']})
    subprocess.run(['import', '-window', 'root', os.path.join(OUT, 'f%04d.png' % i)], check=True)
    i += 1


for b, sx, sy, tag in seq: step(b, sx, sy, tag)
while player(e)['x'] < 712:
    step(0, 80, 0, 'stop-and-go: push Lakilester right')
    step(0, 0, 0, 'stop-and-go: push Lakilester right')
    step(0, 0, 0, 'stop-and-go: push Lakilester right')
for k in range(10): step(0, 0, -80, 'down')
for k in range(4): step(0, 80, 0, 'right, to the pillar corner line')
step(0, 0, 20, 'walk up slowly')
step(CD, 0, 20, 'C-down while Lakilester is fast')
for k in range(45): step(0, 0, 0, 'mount: Mario lands behind the mirror')
json.dump(log, open(os.path.join(OUT, 'log.json'), 'w'))
print('end', log[-1])
