"""Probe simple endings from the top-right corner: normalize Mario into the very top-right corner (hold up U frames,
then right R frames), then a sequence of (buttons, direction, frames) steps; print Mario each frame with y/action and
whether he is in the usable corner zone. usage: rta_probe.py '<json [["A"|"", dir, n], ...]>'"""
import json, math, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
DIRS = {'up': 270, 'down': 90, 'left': 180, 'right': 0, 'none': None}
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rprobe')
def laki():
    for n in npcs(e):
        if n['id'] == -4: return n
def in_zone(x, z, y):
    return (abs(y + 20) < 0.5 and -145.5 <= z <= -72 and x >= 871.5 and x <= 871.5 + 0.175 * (-72 - z) and math.hypot(x - 530.8, z + 13) >= 370.4)
e.load(os.environ.get('START', 'states/pra01_topright_rj.st')); e.step(0, 0, 0, 2)
for i in range(int(os.environ.get('U', 8))): e.step(0, *stick_for(270, 80), 2)
for i in range(int(os.environ.get('R', 8))): e.step(0, *stick_for(0, 80), 2)
p = player(e); print('corner: Mario (%.1f, %.1f, %.1f)  Laki x %.1f' % (p['x'], p['y'], p['z'], laki()['x']))
f = 0
for btn, d, n in json.loads(sys.argv[1]):
    s = stick_for(DIRS[d], 80) if DIRS[d] is not None else (0, 0)
    for i in range(n):
        b = (0x80 if btn == 'A' and i < 12 else 0)
        e.step(b, *s, 2); p = player(e)
        print('%3d %s %-5s Mario (%7.2f, %6.2f, %7.2f) act %2d %s' % (f, btn or ' ', d, p['x'], p['y'], p['z'], p['action'], 'ZONE' if in_zone(p['x'], p['z'], p['y']) else ''))
        f += 1
