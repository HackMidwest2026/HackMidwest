"""Place Mario on the second step at (X, Z), then apply (direction, frames) steps; print where he ends after each step.
usage: rta_place.py X Z '<json [[dir, n], ...]>'"""
import json, os, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
from corner_sweep import stick_for
DIRS = {'up': 270, 'down': 90, 'left': 180, 'right': 0, 'none': None, 'upleft': 225, 'upright': 315}
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/rplace')
e.load('states/pra01_top_start.st'); e.step(0, 0, 0, 2)
e.wf32(PLAYER + PS_POS, float(sys.argv[1])); e.wf32(PLAYER + PS_POS + 4, -17.0); e.wf32(PLAYER + PS_POS + 8, float(sys.argv[2]))
for i in range(15): e.step(0, 0, 0, 2)
p = player(e); print('start (%.2f, %.2f, %.2f)' % (p['x'], p['y'], p['z']))
for d, n in json.loads(sys.argv[3]):
    s = stick_for(DIRS[d], 80) if DIRS[d] is not None else (0, 0)
    for i in range(n): e.step(0, *s, 2)
    p = player(e); print('after %-7s %2d: (%.2f, %.2f, %.2f) act %d' % (d, n, p['x'], p['y'], p['z'], p['action']))
