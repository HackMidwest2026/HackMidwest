"""screenshot after loading a state and stepping inputs: shot.py <state> <out.png> '<json [[b,sx,sy,n],...]>'"""
import json, os, subprocess, sys
os.environ.setdefault('PM_ROM', 'pm-jp.z64')
from emu import Emu
from pm import *
e = Emu(os.environ['PM_ROM'], '/dev/shm/pmbot/shot')
e.load(sys.argv[1])
for b, sx, sy, n in json.loads(sys.argv[3] if len(sys.argv) > 3 else '[[0,0,0,5]]'):
    for i in range(n): e.step(b if i == 0 else 0, sx, sy, 2)
p = player(e); print('mario %.1f %.1f %.1f' % (p['x'], p['y'], p['z']))
subprocess.run(['import', '-window', 'root', '-crop', '592x400+104+100', sys.argv[2]], check=True)
